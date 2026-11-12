import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Subject, of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { HistorialComponent } from './historial.component';
import { HistorialService } from './historial.service';
import { RegistroCarga } from './registro-carga.model';

const haceHoras = (horas: number) => new Date(Date.now() - horas * 3_600_000).toISOString();

const REGISTROS: RegistroCarga[] = [
  { id: 3, carro_id: 1, carro_numero: 'P001A', contenedor_elemento: '100333', cargada_en: haceHoras(5), recibida_en: null },
  { id: 2, carro_id: 2, carro_numero: 'P002A', contenedor_elemento: '100222', cargada_en: haceHoras(30), recibida_en: haceHoras(6) },
];

describe('HistorialComponent', () => {
  let fixture: ComponentFixture<HistorialComponent>;
  let el: HTMLElement;
  let listar: ReturnType<typeof vi.fn>;

  async function crear(respuesta: unknown = of(REGISTROS)) {
    listar = vi.fn().mockReturnValue(respuesta);
    await TestBed.configureTestingModule({
      imports: [HistorialComponent],
      providers: [{ provide: HistorialService, useValue: { listar } }],
    }).compileComponents();
    fixture = TestBed.createComponent(HistorialComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    el = fixture.nativeElement;
  }

  const filas = () => Array.from(el.querySelectorAll('li.registro'));
  const campo = (nombre: string) => el.querySelector<HTMLInputElement>(`input[name="${nombre}"]`)!;

  function escribir(nombre: string, valor: string) {
    campo(nombre).value = valor;
    campo(nombre).dispatchEvent(new Event('input'));
  }

  async function buscar() {
    el.querySelector<HTMLFormElement>('form')!.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    await fixture.whenStable();
  }

  it('al abrir, pide los viajes más recientes sin filtros', async () => {
    await crear();
    expect(listar).toHaveBeenCalledWith({ numero: '', contenedor: '' });
  });

  it('muestra cada viaje con su carro y su contenedor elemento', async () => {
    await crear();
    expect(filas().length).toBe(2);
    expect(filas()[0].textContent).toContain('P001A');
    expect(filas()[0].textContent).toContain('Contenedor 100333');
  });

  it('un viaje en curso dice que sigue en tránsito y cuánto lleva', async () => {
    await crear();
    expect(filas()[0].textContent).toContain('Aún en tránsito');
    expect(filas()[0].querySelector('.insignia')?.textContent?.trim()).toBe('5 h');
    expect(filas()[0].querySelector('.insignia')?.getAttribute('data-estado')).toBe('en_transito');
  });

  it('un viaje terminado muestra la fecha de recepción y cuánto duró', async () => {
    await crear();
    expect(filas()[1].textContent).toContain('Recibido:');
    expect(filas()[1].textContent).not.toContain('Aún en tránsito');
    // Cargado hace 30 h y recibido hace 6 h: el viaje duró 24 h, es decir, 1 día.
    expect(filas()[1].querySelector('.insignia')?.textContent?.trim()).toBe('1 d');
    expect(filas()[1].querySelector('.insignia')?.getAttribute('data-estado')).toBe('disponible');
  });

  it('cuenta los viajes', async () => {
    await crear();
    expect(el.querySelector('.detalle')?.textContent).toContain('2 viajes');
  });

  it('en singular cuando hay uno solo', async () => {
    await crear(of([REGISTROS[0]]));
    expect(el.querySelector('.detalle')?.textContent).toContain('1 viaje');
    expect(el.querySelector('.detalle')?.textContent).not.toContain('1 viajes');
  });

  it('avisa cuando solo se muestran los más recientes', async () => {
    const muchos = Array.from({ length: 100 }, (_, i) => ({ ...REGISTROS[1], id: i + 1 }));
    await crear(of(muchos));
    expect(el.querySelector('.detalle')?.textContent).toContain('los 100 más recientes');
  });

  it('avisa cuando no hay viajes', async () => {
    await crear(of([]));
    expect(el.textContent).toContain('No hay viajes para mostrar');
  });

  it('muestra un aviso mientras carga', async () => {
    const pendiente = new Subject<RegistroCarga[]>();
    await crear(pendiente);
    expect(el.textContent).toContain('Cargando historial');

    pendiente.next(REGISTROS);
    fixture.detectChanges();
    expect(el.textContent).not.toContain('Cargando historial');
    expect(filas().length).toBe(2);
  });

  it('muestra el mensaje de error si falla', async () => {
    await crear(throwError(() => ({ status: 500 })));
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('No se pudo cargar el historial');
    expect(el.textContent).not.toContain('Cargando historial');
  });

  describe('búsqueda', () => {
    it('busca por el número del carro, sin espacios sobrantes', async () => {
      await crear();
      escribir('numero', '  P001A ');
      await buscar();

      expect(listar).toHaveBeenLastCalledWith({ numero: 'P001A', contenedor: '' });
    });

    it('busca por el contenedor elemento', async () => {
      await crear();
      escribir('contenedor', '100222');
      await buscar();

      expect(listar).toHaveBeenLastCalledWith({ numero: '', contenedor: '100222' });
    });

    it('combina los dos campos', async () => {
      await crear();
      escribir('numero', 'P002A');
      escribir('contenedor', '100222');
      await buscar();

      expect(listar).toHaveBeenLastCalledWith({ numero: 'P002A', contenedor: '100222' });
    });

    it('muestra el resultado de la búsqueda', async () => {
      await crear();
      listar.mockReturnValueOnce(of([REGISTROS[1]]));
      escribir('contenedor', '100222');
      await buscar();

      expect(filas().length).toBe(1);
      expect(filas()[0].textContent).toContain('P002A');
    });

    it('conserva la lista y avisa si la búsqueda falla', async () => {
      await crear();
      listar.mockReturnValueOnce(throwError(() => ({ status: 500 })));
      await buscar();

      expect(filas().length).toBe(2);
      expect(el.querySelector('[role="alert"]')).not.toBeNull();
    });
  });
});
