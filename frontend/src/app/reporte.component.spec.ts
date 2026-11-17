import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Subject, of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { DescargaService } from './descarga.service';
import { FilaCarroReporte, ReporteCarros } from './reporte.model';
import { ReporteComponent } from './reporte.component';
import { ReporteService } from './reporte.service';

const carro = (datos: Partial<FilaCarroReporte>): FilaCarroReporte => ({
  carro_fisico: 'P056',
  lado: 'A',
  carro: 'P056A',
  viajes: 2,
  ultimo_contenedor: '848000001ZP056A',
  calidad: '1 (AA)',
  situacion: 'En DTY (salió de WIPB4)',
  horas_en_situacion: 5.5,
  horas_promedio_en_rcv: 2,
  horas_promedio_en_wip: 4,
  situacion_sistema: 'Liberado en el sistema',
  viajes_en_sistema: 1,
  horas_en_dty: 8,
  dty_abierto: false,
  horas_promedio_en_dty: 8,
  ...datos,
});

const REPORTE: ReporteCarros = {
  corte: '16/11/2026 11:07',
  resumen: [
    { indicador: 'Carros físicos (lados A y B juntos)', valor: 246 },
    { indicador: 'El que más lleva en RCV01 sin moverse', valor: 'P019A: 80.8 h' },
  ],
  tablas: [
    { titulo: 'Horas en WIP según el WIP de salida', columna: 'WIP', filas: [{ clave: 'WIPB4', viajes: 180, promedio: 2.4, maximo: 12.6 }] },
    { titulo: 'Tabla vacía', columna: 'WIP', filas: [] },
  ],
  carros: [
    carro({}),
    carro({ lado: 'B', carro: 'P056B', horas_en_dty: 9.1, dty_abierto: true, situacion_sistema: 'Cargado en el sistema, sin liberar', viajes_en_sistema: 1 }),
    carro({ carro_fisico: 'P057', carro: 'P057A', horas_en_situacion: null, horas_en_dty: null, situacion_sistema: 'Sin registro en este sistema', viajes_en_sistema: 0 }),
  ],
};

describe('ReporteComponent', () => {
  let fixture: ComponentFixture<ReporteComponent>;
  let el: HTMLElement;
  let generar: ReturnType<typeof vi.fn>;
  let descargarExcel: ReturnType<typeof vi.fn>;
  let guardar: ReturnType<typeof vi.fn>;
  const archivo = new File(['contenido'], 'movimientos.xlsx');

  async function crear(respuesta: unknown = of(REPORTE)) {
    generar = vi.fn().mockReturnValue(respuesta);
    descargarExcel = vi.fn().mockReturnValue(of(new Blob(['xlsx'])));
    guardar = vi.fn(); // la descarga real no se ejecuta: solo importa que se pida guardar el archivo
    await TestBed.configureTestingModule({
      imports: [ReporteComponent],
      providers: [
        { provide: ReporteService, useValue: { generar, descargarExcel } },
        { provide: DescargaService, useValue: { guardar } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(ReporteComponent);
    fixture.detectChanges();
    el = fixture.nativeElement;
  }

  const boton = (texto: string) =>
    Array.from(el.querySelectorAll<HTMLButtonElement>('button')).find((b) => b.textContent?.includes(texto));

  async function elegirArchivo(elegido: File | null = archivo) {
    const campo = el.querySelector<HTMLInputElement>('input[type="file"]')!;
    Object.defineProperty(campo, 'files', { value: elegido ? [elegido] : [], configurable: true });
    campo.dispatchEvent(new Event('change'));
    fixture.detectChanges();
  }

  async function enviar() {
    el.querySelector<HTMLFormElement>('form')!.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  }

  /** Las filas de la tabla "Por carro", que es la última de la pantalla. */
  const filas = () => {
    const tablas = el.querySelectorAll('.tabla');
    const porCarro = tablas[tablas.length - 1];
    return Array.from(porCarro.querySelectorAll('tbody tr')).filter((fila) => !fila.querySelector('.vacio'));
  };

  it('no deja generar el reporte sin elegir un archivo', async () => {
    await crear();
    expect(boton('Generar reporte')!.disabled).toBe(true);
    await elegirArchivo();
    expect(boton('Generar reporte')!.disabled).toBe(false);
  });

  it('manda el archivo elegido a la API', async () => {
    await crear();
    await elegirArchivo();
    await enviar();
    expect(generar).toHaveBeenCalledWith(archivo);
  });

  it('no manda nada si se envía sin archivo', async () => {
    await crear();
    await enviar();
    expect(generar).not.toHaveBeenCalled();
  });

  it('muestra el resumen con la hora de corte', async () => {
    await crear();
    await elegirArchivo();
    await enviar();
    expect(el.textContent).toContain('16/11/2026 11:07');
    expect(el.querySelector('.resumen')?.textContent).toContain('Carros físicos (lados A y B juntos)');
    expect(el.querySelector('.resumen')?.textContent).toContain('P019A: 80.8 h');
  });

  it('muestra las tablas con datos y omite las vacías', async () => {
    await crear();
    await elegirArchivo();
    await enviar();
    expect(el.textContent).toContain('Horas en WIP según el WIP de salida');
    expect(el.textContent).toContain('WIPB4');
    expect(el.textContent).not.toContain('Tabla vacía');
  });

  it('muestra cada lado de carro con su situación en NOW y en este sistema', async () => {
    await crear();
    await elegirArchivo();
    await enviar();
    const [primera, segunda, tercera] = filas().map((fila) => fila.textContent ?? '');
    expect(primera).toContain('P056A');
    expect(primera).toContain('En DTY (salió de WIPB4)');
    expect(primera).toContain('Liberado en el sistema');
    expect(primera).toContain('8 h');
    expect(segunda).toContain('9.1 h (sin liberar)');
    expect(tercera).toContain('Sin registro en este sistema');
    expect(tercera).toContain('—');
  });

  it('busca por carro', async () => {
    await crear();
    await elegirArchivo();
    await enviar();
    const caja = el.querySelector<HTMLInputElement>('input[name="buscar"]')!;
    caja.value = 'p057';
    caja.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    expect(filas().length).toBe(1);
    expect(filas()[0].textContent).toContain('P057A');
    expect(el.textContent).toContain('1 de 3 carros');
  });

  it('avisa si la búsqueda no encuentra nada', async () => {
    await crear();
    await elegirArchivo();
    await enviar();
    const caja = el.querySelector<HTMLInputElement>('input[name="buscar"]')!;
    caja.value = 'ZZZ';
    caja.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    expect(el.textContent).toContain('No hay carros para mostrar');
  });

  it('mientras genera, avisa y no deja enviar otra vez', async () => {
    const pendiente = new Subject<ReporteCarros>();
    await crear(pendiente);
    await elegirArchivo();
    await enviar();
    expect(boton('Generando')!.disabled).toBe(true);
    pendiente.next(REPORTE);
    pendiente.complete();
    fixture.detectChanges();
    expect(boton('Generar reporte')!.disabled).toBe(false);
  });

  it('muestra el mensaje de la API si el archivo no sirve y no deja un reporte a medias', async () => {
    await crear(throwError(() => ({ status: 422, error: { detail: 'El archivo no es un Excel (.xlsx) válido.' } })));
    await elegirArchivo();
    await enviar();
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('no es un Excel');
    expect(el.querySelector('.resumen')).toBeNull();
  });

  it('cambiar de archivo borra el reporte anterior', async () => {
    await crear();
    await elegirArchivo();
    await enviar();
    expect(el.querySelector('.resumen')).toBeTruthy();

    await elegirArchivo(new File(['otro'], 'otro.xlsx'));
    expect(el.querySelector('.resumen')).toBeNull();
  });

  it('quitar el archivo vuelve a bloquear el envío', async () => {
    await crear();
    await elegirArchivo();
    await elegirArchivo(null);
    expect(boton('Generar reporte')!.disabled).toBe(true);
  });

  describe('descarga del Excel', () => {
    it('solo se ofrece cuando ya hay un reporte', async () => {
      await crear();
      await elegirArchivo();
      expect(boton('Descargar Excel')).toBeUndefined();
      await enviar();
      expect(boton('Descargar Excel')).toBeTruthy();
    });

    it('pide el Excel con el mismo archivo y lo guarda', async () => {
      await crear();
      await elegirArchivo();
      await enviar();

      boton('Descargar Excel')!.click();
      fixture.detectChanges();

      expect(descargarExcel).toHaveBeenCalledWith(archivo);
      expect(guardar).toHaveBeenCalledWith(expect.any(Blob), 'reporte_carros.xlsx');
    });

    it('avisa si no se pudo preparar el Excel', async () => {
      await crear();
      descargarExcel.mockReturnValue(throwError(() => new Error('falló')));
      await elegirArchivo();
      await enviar();

      boton('Descargar Excel')!.click();
      fixture.detectChanges();

      expect(el.querySelector('[role="alert"]')?.textContent).toContain('No se pudo preparar el Excel');
    });
  });
});
