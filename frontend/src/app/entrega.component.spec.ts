import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Subject, of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { Carro } from './carro.model';
import { CarrosService, ContenedorNoEncontrado } from './carros.service';
import { EntregaComponent, LIMITE_LISTA } from './entrega.component';

const DISPONIBLE: Carro = {
  id: 1,
  numero: 'P001A',
  tipo: 'poy',
  estado: 'disponible',
  contenedor_elemento: null,
  estado_desde: '2026-11-12T12:00:00Z',
};

const hace = (horas: number) => new Date(Date.now() - horas * 3_600_000).toISOString();

const EN_TRANSITO: Carro[] = [
  { id: 1, numero: 'P001A', tipo: 'poy', estado: 'en_transito', contenedor_elemento: '100123', estado_desde: hace(5) },
  { id: 2, numero: 'P002B', tipo: 'poy', estado: 'en_transito', contenedor_elemento: '100222', estado_desde: hace(30) },
  { id: 3, numero: 'P010A', tipo: 'poy', estado: 'en_transito', contenedor_elemento: null, estado_desde: hace(1) },
];

describe('EntregaComponent', () => {
  let fixture: ComponentFixture<EntregaComponent>;
  let el: HTMLElement;
  let entregarPorContenedor: ReturnType<typeof vi.fn>;
  let listarEnTransito: ReturnType<typeof vi.fn>;
  let entregar: ReturnType<typeof vi.fn>;

  async function crear(respuesta: unknown = of(DISPONIBLE), lista: unknown = of(EN_TRANSITO)) {
    entregarPorContenedor = vi.fn().mockReturnValue(respuesta);
    listarEnTransito = vi.fn().mockReturnValue(lista);
    entregar = vi.fn().mockReturnValue(of({ ...DISPONIBLE, numero: 'P001A' }));
    await TestBed.configureTestingModule({
      imports: [EntregaComponent],
      providers: [{ provide: CarrosService, useValue: { entregarPorContenedor, listarEnTransito, entregar } }],
    }).compileComponents();
    fixture = TestBed.createComponent(EntregaComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    el = fixture.nativeElement;
  }

  const campo = () => el.querySelector<HTMLInputElement>('input[name="contenedor"]')!;

  function escribir(valor: string) {
    campo().value = valor;
    campo().dispatchEvent(new Event('input'));
  }

  async function enviar() {
    el.querySelector<HTMLFormElement>('form')!.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    await fixture.whenStable();
  }

  it('el formulario de arriba pide solo el contenedor elemento, no el número del carro', async () => {
    await crear();
    expect(el.querySelector('form')!.querySelectorAll('input').length).toBe(1);
    expect(el.querySelector('label')?.textContent).toContain('Contenedor elemento');
    expect(el.querySelector('input[name="carro"]')).toBeNull();
  });

  it('abre con el cursor en el campo, listo para escanear', async () => {
    await crear();
    expect(document.activeElement).toBe(campo());
  });

  it('recibe el carro con el contenedor escrito, sin espacios sobrantes', async () => {
    await crear();
    escribir('  100123 ');
    await enviar();

    expect(entregarPorContenedor).toHaveBeenCalledWith('100123');
  });

  it('confirma con el número del carro que quedó libre, limpia el campo y vuelve a él', async () => {
    await crear();
    escribir('100123');
    await enviar();

    const mensaje = el.querySelector('[role="status"]')?.textContent;
    expect(mensaje).toContain('Carro P001A recibido');
    expect(mensaje).toContain('contenedor 100123');
    expect(campo().value).toBe('');
    expect(document.activeElement).toBe(campo());
  });

  it('vacía el campo aunque el escaneo y el envío ocurran sin refrescar la pantalla entre medio', async () => {
    await crear();
    escribir('100123');
    el.querySelector<HTMLFormElement>('form')!.dispatchEvent(new Event('submit'));

    expect(campo().value).toBe('');
  });

  it('pide un código si el campo está vacío', async () => {
    await crear();
    await enviar();

    expect(entregarPorContenedor).not.toHaveBeenCalled();
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('Escribe o escanea');
  });

  it('muestra el mensaje de la API y conserva lo escrito si no se puede recibir', async () => {
    const fallo = { status: 409, error: { detail: 'El carro no está en tránsito' } };
    await crear(throwError(() => fallo));
    escribir('100123');
    await enviar();

    expect(el.querySelector('[role="alert"]')?.textContent).toContain('El carro no está en tránsito');
    expect(el.querySelector('[role="status"]')).toBeNull();
    expect(campo().value).toBe('100123');
  });

  it('avisa si ningún carro en tránsito lleva ese contenedor', async () => {
    await crear(throwError(() => new ContenedorNoEncontrado('999999')));
    escribir('999999');
    await enviar();

    expect(el.querySelector('[role="alert"]')?.textContent).toContain(
      'No hay ningún carro en tránsito con el contenedor elemento 999999',
    );
  });

  describe('liberar por carro, sin escáner', () => {
    const filas = () => Array.from(el.querySelectorAll('li.carro'));
    const buscar = (texto: string) => {
      const caja = el.querySelector<HTMLInputElement>('input[name="buscar"]')!;
      caja.value = texto;
      caja.dispatchEvent(new Event('input'));
      fixture.detectChanges();
    };
    const boton = (texto: string, dentro: ParentNode = el) =>
      Array.from(dentro.querySelectorAll<HTMLButtonElement>('button')).find((b) => b.textContent?.trim() === texto);

    async function liberarPrimero() {
      boton('Liberar', filas()[0])!.click();
      fixture.detectChanges();
      boton('Sí, liberar')!.click();
      fixture.detectChanges();
      await fixture.whenStable();
    }

    it('trae la lista de los carros en tránsito al abrir', async () => {
      await crear();
      expect(listarEnTransito).toHaveBeenCalled();
      expect(filas().length).toBe(3);
      expect(filas()[0].textContent).toContain('P001A');
      expect(filas()[0].textContent).toContain('Contenedor 100123');
      expect(filas()[0].textContent).toContain('En tránsito hace 5 h');
    });

    it('un carro sin contenedor registrado se muestra sin esa línea', async () => {
      await crear();
      expect(filas()[2].textContent).not.toContain('Contenedor');
    });

    it('busca por carro, sin importar mayúsculas', async () => {
      await crear();
      buscar('p002');
      expect(filas().length).toBe(1);
      expect(filas()[0].textContent).toContain('P002B');
      expect(el.textContent).toContain('1 de 3 carros en tránsito');
    });

    it('avisa si la búsqueda no encuentra ningún carro', async () => {
      await crear();
      buscar('ZZZ');
      expect(el.textContent).toContain('No hay carros en tránsito para mostrar');
    });

    it('pide confirmación antes de liberar, porque no se puede deshacer', async () => {
      await crear();
      boton('Liberar', filas()[0])!.click();
      fixture.detectChanges();

      expect(entregar).not.toHaveBeenCalled();
      expect(filas()[0].textContent).toContain('¿Liberar P001A?');
    });

    it('cancelar la confirmación no libera nada y vuelve al botón', async () => {
      await crear();
      boton('Liberar', filas()[0])!.click();
      fixture.detectChanges();
      boton('Cancelar')!.click();
      fixture.detectChanges();

      expect(entregar).not.toHaveBeenCalled();
      expect(boton('Liberar', filas()[0])).toBeTruthy();
    });

    it('libera el carro elegido por su id, avisa y vuelve a pedir la lista', async () => {
      await crear();
      await liberarPrimero();

      expect(entregar).toHaveBeenCalledWith(1);
      expect(el.querySelector('section [role="status"]')?.textContent).toContain('Carro P001A liberado');
      expect(listarEnTransito).toHaveBeenCalledTimes(2);
    });

    it('muestra el mensaje de la API si no se pudo liberar y deja la confirmación abierta', async () => {
      await crear();
      entregar.mockReturnValue(throwError(() => ({ status: 409, error: { detail: 'El carro no está en tránsito' } })));
      await liberarPrimero();

      expect(el.querySelector('section [role="alert"]')?.textContent).toContain('El carro no está en tránsito');
      expect(filas()[0].textContent).toContain('¿Liberar P001A?');
    });

    it('mientras libera no deja confirmar otra vez', async () => {
      await crear();
      const pendiente = new Subject<Carro>();
      entregar.mockReturnValue(pendiente);
      boton('Liberar', filas()[0])!.click();
      fixture.detectChanges();
      boton('Sí, liberar')!.click();
      fixture.detectChanges();

      expect(boton('Sí, liberar')!.disabled).toBe(true);
    });

    it('recibir con el contenedor también actualiza la lista', async () => {
      await crear();
      escribir('100123');
      await enviar();
      expect(listarEnTransito).toHaveBeenCalledTimes(2);
    });

    it('el botón Actualizar vuelve a pedir la lista', async () => {
      await crear();
      boton('Actualizar')!.click();
      fixture.detectChanges();
      expect(listarEnTransito).toHaveBeenCalledTimes(2);
    });

    it('si la lista no carga, lo dice y la pantalla sigue sirviendo para escanear', async () => {
      await crear(of(DISPONIBLE), throwError(() => ({ status: 0 })));
      expect(el.querySelector('section [role="alert"]')?.textContent).toContain('No se pudo conectar con el servidor');
      escribir('100123');
      await enviar();
      expect(entregarPorContenedor).toHaveBeenCalledWith('100123');
    });

    it('con muchos carros muestra los primeros y pide acotar con la búsqueda', async () => {
      const muchos = Array.from({ length: LIMITE_LISTA + 5 }, (_, i) => ({
        ...EN_TRANSITO[0],
        id: i + 1,
        numero: `P${String(i + 1).padStart(3, '0')}A`,
      }));
      await crear(of(DISPONIBLE), of(muchos));

      expect(filas().length).toBe(LIMITE_LISTA);
      expect(el.textContent).toContain(`Se muestran los primeros ${LIMITE_LISTA}`);
      buscar('P055');
      expect(filas().length).toBe(1);
    });
  });
});
