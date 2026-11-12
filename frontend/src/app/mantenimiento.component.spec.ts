import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { Carro } from './carro.model';
import { CarroNoExiste, CarrosService } from './carros.service';
import { MantenimientoComponent } from './mantenimiento.component';
import { MantenimientoService } from './mantenimiento.service';

const hace = (horas: number) => new Date(Date.now() - horas * 3_600_000).toISOString();

const carro = (id: number, estado: Carro['estado'], horas: number): Carro => ({
  id,
  numero: `C-00${id}`,
  tipo: 'poy',
  estado,
  contenedor_elemento: null,
  estado_desde: hace(horas),
});

const LISTA: Carro[] = [
  carro(1, 'disponible', 1),
  carro(2, 'en_mantenimiento', 2),
  carro(3, 'en_transito', 5),
  carro(4, 'en_mantenimiento', 30),
];

describe('MantenimientoComponent', () => {
  let fixture: ComponentFixture<MantenimientoComponent>;
  let el: HTMLElement;
  let listar: ReturnType<typeof vi.fn>;
  let iniciarPorNumero: ReturnType<typeof vi.fn>;
  let finalizar: ReturnType<typeof vi.fn>;

  async function crear(opciones: { lista?: unknown; entrada?: unknown; salida?: unknown } = {}) {
    listar = vi.fn().mockReturnValue(opciones.lista ?? of(LISTA));
    iniciarPorNumero = vi.fn().mockReturnValue(opciones.entrada ?? of({}));
    finalizar = vi.fn().mockReturnValue(opciones.salida ?? of({}));
    await TestBed.configureTestingModule({
      imports: [MantenimientoComponent],
      providers: [
        { provide: CarrosService, useValue: { listar } },
        { provide: MantenimientoService, useValue: { iniciarPorNumero, finalizar } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(MantenimientoComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    el = fixture.nativeElement;
  }

  const campo = () => el.querySelector<HTMLInputElement>('input[name="carro"]')!;
  const filas = () => Array.from(el.querySelectorAll('li.carro'));
  const numeros = () => filas().map((fila) => fila.querySelector('strong')?.textContent);

  function escribir(valor: string) {
    campo().value = valor;
    campo().dispatchEvent(new Event('input'));
  }

  async function registrarEntrada() {
    el.querySelector<HTMLFormElement>('form')!.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    await fixture.whenStable();
  }

  async function darSalida(posicion = 0) {
    el.querySelectorAll<HTMLButtonElement>('li.carro button')[posicion].click();
    fixture.detectChanges();
    await fixture.whenStable();
  }

  describe('lista de carros en mantenimiento', () => {
    it('muestra solo los carros que están en mantenimiento', async () => {
      await crear();
      expect(numeros()).toEqual(['C-004', 'C-002']);
      expect(el.querySelector('h2')?.textContent).toContain('(2)');
    });

    it('muestra primero los que llevan más tiempo y desde cuándo', async () => {
      await crear();
      const tiempos = Array.from(el.querySelectorAll('li.carro small')).map((t) => t.textContent?.trim());
      expect(tiempos).toEqual(['Desde hace 1 d 6 h', 'Desde hace 2 h']);
    });

    it('avisa cuando no hay ninguno', async () => {
      await crear({ lista: of([carro(1, 'disponible', 1)]) });
      expect(el.textContent).toContain('No hay carros en mantenimiento');
    });

    it('avisa si no se pudo cargar la lista', async () => {
      await crear({ lista: throwError(() => ({ status: 500 })) });
      expect(el.querySelector('[role="alert"]')?.textContent).toContain('No se pudo cargar la lista de carros');
    });
  });

  describe('registrar entrada', () => {
    it('abre con el cursor en el campo del carro, listo para escanear', async () => {
      await crear();
      expect(document.activeElement).toBe(campo());
    });

    it('registra la entrada del carro con el número escrito, sin espacios sobrantes', async () => {
      await crear();
      escribir('  C-001 ');
      await registrarEntrada();

      expect(iniciarPorNumero).toHaveBeenCalledWith('C-001');
    });

    it('confirma, vacía el campo, vuelve a él y recarga la lista', async () => {
      await crear();
      escribir('C-001');
      await registrarEntrada();

      expect(el.querySelector('[role="status"]')?.textContent).toContain('Carro C-001 registrado en mantenimiento');
      expect(campo().value).toBe('');
      expect(document.activeElement).toBe(campo());
      expect(listar).toHaveBeenCalledTimes(2);
    });

    it('pide un número si el campo está vacío', async () => {
      await crear();
      await registrarEntrada();

      expect(iniciarPorNumero).not.toHaveBeenCalled();
      expect(el.querySelector('[role="alert"]')?.textContent).toContain('Escribe o escanea');
    });

    it('muestra el mensaje de la API si el carro no está disponible', async () => {
      const fallo = { status: 409, error: { detail: 'Solo un carro disponible puede entrar a mantenimiento' } };
      await crear({ entrada: throwError(() => fallo) });
      escribir('C-003');
      await registrarEntrada();

      expect(el.querySelector('[role="alert"]')?.textContent).toContain('Solo un carro disponible');
      expect(campo().value).toBe('C-003');
    });

    it('avisa si el carro no existe', async () => {
      await crear({ entrada: throwError(() => new CarroNoExiste('C-999')) });
      escribir('C-999');
      await registrarEntrada();

      expect(el.querySelector('[role="alert"]')?.textContent).toContain('No existe un carro con el número C-999');
    });
  });

  describe('dar salida', () => {
    it('registra la salida del carro de la fila que se toca', async () => {
      await crear();
      await darSalida(0); // la primera fila es C-004

      expect(finalizar).toHaveBeenCalledWith(4);
    });

    it('confirma y recarga la lista', async () => {
      await crear();
      listar.mockReturnValueOnce(of([carro(2, 'en_mantenimiento', 2), carro(4, 'disponible', 0)]));
      await darSalida(0);

      expect(el.querySelector('[role="status"]')?.textContent).toContain(
        'Carro C-004 salió de mantenimiento y está disponible',
      );
      expect(listar).toHaveBeenCalledTimes(2);
      expect(numeros()).toEqual(['C-002']);
    });

    it('muestra el mensaje de la API si no se puede dar salida', async () => {
      const fallo = { status: 409, error: { detail: 'El carro no está en mantenimiento' } };
      await crear({ salida: throwError(() => fallo) });
      await darSalida(0);

      expect(el.querySelector('[role="alert"]')?.textContent).toContain('El carro no está en mantenimiento');
      expect(listar).toHaveBeenCalledTimes(1);
    });
  });
});
