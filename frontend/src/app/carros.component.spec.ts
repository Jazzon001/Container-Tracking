import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Subject, of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { Carro } from './carro.model';
import { CarrosComponent, INTERVALO_ACTUALIZACION_MS } from './carros.component';
import { CarrosService } from './carros.service';

const hace = (horas: number) => new Date(Date.now() - horas * 3_600_000).toISOString();

const CARROS: Carro[] = [
  { id: 1, numero: 'C-001', tipo: 'poy', estado: 'disponible', contenedor_elemento: null, estado_desde: hace(1) },
  { id: 2, numero: 'C-002', tipo: 'poy', estado: 'en_transito', contenedor_elemento: '100123', estado_desde: hace(3) },
  { id: 3, numero: 'D-003', tipo: 'dty', estado: 'disponible', contenedor_elemento: null, estado_desde: hace(2) },
];

describe('CarrosComponent', () => {
  let fixture: ComponentFixture<CarrosComponent>;
  let el: HTMLElement;
  let listar: ReturnType<typeof vi.fn>;

  async function crear(respuesta: unknown, intervaloMs = 600_000) {
    listar = vi.fn().mockReturnValue(respuesta);
    await TestBed.configureTestingModule({
      imports: [CarrosComponent],
      providers: [
        { provide: CarrosService, useValue: { listar } },
        { provide: INTERVALO_ACTUALIZACION_MS, useValue: intervaloMs },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(CarrosComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    el = fixture.nativeElement;
  }

  const tarjeta = (estado: string) => el.querySelector<HTMLButtonElement>(`.tarjeta[data-estado="${estado}"]`)!;
  const filas = () => el.querySelectorAll('.carro');
  const numeros = () => Array.from(filas()).map((fila) => fila.querySelector('strong')?.textContent);

  it('muestra los carros con su estado', async () => {
    await crear(of(CARROS));
    expect(filas().length).toBe(3);
    expect(el.querySelector('.carro')?.textContent).toContain('C-001');
    expect(el.querySelector('.carro .insignia')?.textContent).toContain('Disponible');
  });

  it('cuenta los carros de cada estado', async () => {
    await crear(of(CARROS));
    expect(tarjeta('disponible').textContent).toContain('2');
    expect(tarjeta('en_transito').textContent).toContain('1');
    expect(tarjeta('en_mantenimiento').textContent).toContain('0');
    expect(el.textContent).toContain('3 carros en total');
  });

  it('muestra el contenedor elemento solo en los carros que lo tienen', async () => {
    await crear(of(CARROS));
    expect(el.textContent).toContain('Contenedor 100123');
    expect(el.querySelectorAll('small:not(.tiempo)').length).toBe(1);
  });

  it('muestra desde hace cuánto está cada carro en su estado', async () => {
    await crear(of(CARROS));
    const tiempos = Array.from(el.querySelectorAll('.tiempo')).map((t) => t.textContent?.trim());
    expect(tiempos).toEqual(['Desde hace 1 h', 'Desde hace 3 h', 'Desde hace 2 h']);
  });

  it('muestra un aviso mientras carga', async () => {
    const pendiente = new Subject<Carro[]>();
    await crear(pendiente);
    expect(el.textContent).toContain('Cargando');

    pendiente.next(CARROS);
    fixture.detectChanges();
    expect(el.textContent).not.toContain('Cargando');
    expect(filas().length).toBe(3);
  });

  it('avisa cuando no hay carros', async () => {
    await crear(of([]));
    expect(el.textContent).toContain('No hay carros para mostrar');
  });

  it('muestra un error si la API falla', async () => {
    await crear(throwError(() => ({ status: 500 })));
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('No se pudieron cargar los carros');
    expect(el.textContent).not.toContain('Cargando');
  });

  describe('filtros', () => {
    it('filtra al tocar la tarjeta de un estado', async () => {
      await crear(of(CARROS));
      tarjeta('en_transito').click();
      fixture.detectChanges();

      expect(numeros()).toEqual(['C-002']);
      expect(tarjeta('en_transito').getAttribute('aria-pressed')).toBe('true');
      expect(el.textContent).toContain('Mostrando 1 de 3 carros');
    });

    it('quita el filtro al tocar otra vez la misma tarjeta', async () => {
      await crear(of(CARROS));
      tarjeta('en_transito').click();
      fixture.detectChanges();
      tarjeta('en_transito').click();
      fixture.detectChanges();

      expect(filas().length).toBe(3);
    });

    it('quita los filtros con el botón "Quitar filtros"', async () => {
      await crear(of(CARROS));
      tarjeta('disponible').click();
      fixture.detectChanges();
      el.querySelector<HTMLButtonElement>('.detalle button')!.click();
      fixture.detectChanges();

      expect(filas().length).toBe(3);
      expect(el.textContent).toContain('3 carros en total');
    });

    it('en tránsito muestra primero los que llevan más tiempo', async () => {
      const enTransito = (id: number, horas: number): Carro => ({
        id,
        numero: `C-00${id}`,
        tipo: 'poy',
        estado: 'en_transito',
        contenedor_elemento: `10000${id}`,
        estado_desde: hace(horas),
      });
      // La API los entrega por id: el más reciente primero. La pantalla los reordena.
      await crear(of([enTransito(1, 1), enTransito(2, 50), enTransito(3, 5)]));
      tarjeta('en_transito').click();
      fixture.detectChanges();

      expect(numeros()).toEqual(['C-002', 'C-003', 'C-001']);
    });

    it('en los demás estados conserva el orden de la API', async () => {
      await crear(of(CARROS));
      tarjeta('disponible').click();
      fixture.detectChanges();

      expect(numeros()).toEqual(['C-001', 'D-003']);
    });
  });

  describe('tipo de carro', () => {
    const elegirTipo = (valor: string) => {
      const selector = el.querySelector<HTMLSelectElement>('select[name="tipo"]')!;
      selector.value = valor;
      selector.dispatchEvent(new Event('change'));
      fixture.detectChanges();
    };

    it('muestra el tipo de cada carro', async () => {
      await crear(of(CARROS));
      const tipos = Array.from(el.querySelectorAll('.carro .tipo')).map((t) => t.textContent?.trim());
      expect(tipos).toEqual(['POY', 'POY', 'DTY']);
    });

    it('ofrece todos los tipos para filtrar', async () => {
      await crear(of(CARROS));
      const opciones = Array.from(el.querySelectorAll('select[name="tipo"] option')).map((o) => o.textContent?.trim());
      expect(opciones).toEqual(['Todos', 'POY', 'DTY', 'Twisting']);
    });

    it('muestra solo los carros del tipo elegido', async () => {
      await crear(of(CARROS));
      elegirTipo('dty');

      expect(numeros()).toEqual(['D-003']);
      expect(el.textContent).toContain('Mostrando 1 de 3 carros');
    });

    it('cuenta los estados solo entre los carros del tipo elegido', async () => {
      await crear(of(CARROS));
      elegirTipo('poy');

      expect(tarjeta('disponible').textContent).toContain('1');
      expect(tarjeta('en_transito').textContent).toContain('1');

      elegirTipo('dty');
      expect(tarjeta('disponible').textContent).toContain('1');
      expect(tarjeta('en_transito').textContent).toContain('0');
    });

    it('combina el tipo con el estado', async () => {
      await crear(of(CARROS));
      elegirTipo('poy');
      tarjeta('disponible').click();
      fixture.detectChanges();

      expect(numeros()).toEqual(['C-001']);
    });

    it('al elegir "Todos" vuelve a mostrar todos los tipos', async () => {
      await crear(of(CARROS));
      elegirTipo('dty');
      elegirTipo('');

      expect(filas().length).toBe(3);
    });
  });

  describe('búsqueda por número', () => {
    const buscar = (texto: string) => {
      const caja = el.querySelector<HTMLInputElement>('input[name="buscar"]')!;
      caja.value = texto;
      caja.dispatchEvent(new Event('input'));
      fixture.detectChanges();
    };

    it('muestra los carros cuyo número contiene el texto, sin importar mayúsculas', async () => {
      await crear(of(CARROS));
      buscar('c-00');

      expect(numeros()).toEqual(['C-001', 'C-002']);
    });

    it('encuentra un carro por una parte de su número', async () => {
      await crear(of(CARROS));
      buscar('003');

      expect(numeros()).toEqual(['D-003']);
    });

    it('ignora los espacios al principio y al final', async () => {
      await crear(of(CARROS));
      buscar('  D-003 ');

      expect(numeros()).toEqual(['D-003']);
    });

    it('avisa cuando nada coincide', async () => {
      await crear(of(CARROS));
      buscar('ZZZ');

      expect(el.textContent).toContain('No hay carros para mostrar');
    });

    it('se combina con los demás filtros', async () => {
      await crear(of(CARROS));
      buscar('c-00');
      tarjeta('en_transito').click();
      fixture.detectChanges();

      expect(numeros()).toEqual(['C-002']);
    });

    it('"Quitar filtros" también vacía la búsqueda y el tipo', async () => {
      await crear(of(CARROS));
      buscar('D-003');
      el.querySelector<HTMLButtonElement>('.detalle button')!.click();
      fixture.detectChanges();

      expect(filas().length).toBe(3);
      expect(el.querySelector<HTMLInputElement>('input[name="buscar"]')!.value).toBe('');
    });
  });

  describe('actualización', () => {
    it('muestra la hora de la última actualización', async () => {
      await crear(of(CARROS));
      expect(el.textContent).toMatch(/Actualizado a las \d{1,2}:\d{2}/);
    });

    it('vuelve a consultar al pulsar Actualizar', async () => {
      await crear(of(CARROS));
      expect(listar).toHaveBeenCalledTimes(1);

      const boton = Array.from(el.querySelectorAll<HTMLButtonElement>('.detalle button')).find(
        (b) => b.textContent?.trim() === 'Actualizar',
      )!;
      boton.click();

      expect(listar).toHaveBeenCalledTimes(2);
    });

    it('se actualiza sola cada cierto tiempo', async () => {
      await crear(of(CARROS), 20);
      await new Promise((resolver) => setTimeout(resolver, 110));

      expect(listar.mock.calls.length).toBeGreaterThanOrEqual(3);
    });

    it('conserva la lista y avisa si una actualización falla, y se recupera después', async () => {
      await crear(of(CARROS));
      listar.mockReturnValueOnce(throwError(() => ({ status: 500 })));
      el.querySelector<HTMLButtonElement>('.detalle:last-of-type button')!.click();
      fixture.detectChanges();

      expect(filas().length).toBe(3);
      expect(el.querySelector('[role="alert"]')).not.toBeNull();

      el.querySelector<HTMLButtonElement>('.detalle:last-of-type button')!.click();
      fixture.detectChanges();
      expect(el.querySelector('[role="alert"]')).toBeNull();
    });
  });
});
