import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { Carro } from './carro.model';
import { CarroNoExiste, CarrosService } from './carros.service';
import { CargaComponent } from './carga.component';

const CARGADO: Carro = {
  id: 1,
  numero: 'C-001',
  estado: 'en_transito',
  contenedor_elemento: '100123',
  estado_desde: '2026-11-12T12:00:00Z',
};

describe('CargaComponent', () => {
  let fixture: ComponentFixture<CargaComponent>;
  let el: HTMLElement;
  let cargarPorNumero: ReturnType<typeof vi.fn>;

  async function crear(respuesta: unknown = of(CARGADO)) {
    cargarPorNumero = vi.fn().mockReturnValue(respuesta);
    await TestBed.configureTestingModule({
      imports: [CargaComponent],
      providers: [{ provide: CarrosService, useValue: { cargarPorNumero } }],
    }).compileComponents();
    fixture = TestBed.createComponent(CargaComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    el = fixture.nativeElement;
  }

  const campo = (nombre: string) => el.querySelector<HTMLInputElement>(`input[name="${nombre}"]`)!;

  function escribir(nombre: string, valor: string) {
    campo(nombre).value = valor;
    campo(nombre).dispatchEvent(new Event('input'));
  }

  async function enviar() {
    el.querySelector<HTMLFormElement>('form')!.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    await fixture.whenStable();
  }

  it('abre con el cursor en el campo del carro, listo para escanear', async () => {
    await crear();
    expect(document.activeElement).toBe(campo('carro'));
  });

  it('al terminar el código del carro con Enter, pasa al contenedor sin enviar', async () => {
    await crear();
    const enter = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true });
    campo('carro').dispatchEvent(enter);

    expect(enter.defaultPrevented).toBe(true);
    expect(document.activeElement).toBe(campo('contenedor'));
    expect(cargarPorNumero).not.toHaveBeenCalled();
  });

  it('carga el carro con los códigos escritos', async () => {
    await crear();
    escribir('carro', 'C-001');
    escribir('contenedor', '100123');
    await enviar();

    expect(cargarPorNumero).toHaveBeenCalledWith('C-001', '100123');
  });

  it('recorta espacios de los códigos', async () => {
    await crear();
    escribir('carro', '  C-001 ');
    escribir('contenedor', ' 100123  ');
    await enviar();

    expect(cargarPorNumero).toHaveBeenCalledWith('C-001', '100123');
  });

  it('confirma la carga, limpia los campos y vuelve al campo del carro', async () => {
    await crear();
    escribir('carro', 'C-001');
    escribir('contenedor', '100123');
    await enviar();

    expect(el.querySelector('[role="status"]')?.textContent).toContain('Carro C-001 cargado con el contenedor 100123');
    expect(campo('carro').value).toBe('');
    expect(campo('contenedor').value).toBe('');
    expect(document.activeElement).toBe(campo('carro'));
  });

  it('vacía los campos aunque el escaneo y el envío ocurran sin refrescar la pantalla entre medio', async () => {
    // Un lector de código de barras escribe y envía en milisegundos: el campo no
    // puede depender de que Angular haya refrescado la pantalla antes del envío.
    await crear();
    escribir('carro', 'C-001');
    escribir('contenedor', '100123');
    el.querySelector<HTMLFormElement>('form')!.dispatchEvent(new Event('submit'));

    expect(campo('carro').value).toBe('');
    expect(campo('contenedor').value).toBe('');
  });

  it('pide completar los dos campos si falta alguno', async () => {
    await crear();
    escribir('carro', 'C-001');
    await enviar();

    expect(cargarPorNumero).not.toHaveBeenCalled();
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('Escribe o escanea');
  });

  it('muestra el mensaje de la API si no se puede cargar y conserva lo escrito', async () => {
    const fallo = { status: 409, error: { detail: 'El carro no está disponible para cargarse' } };
    await crear(throwError(() => fallo));
    escribir('carro', 'C-001');
    escribir('contenedor', '100123');
    await enviar();

    expect(el.querySelector('[role="alert"]')?.textContent).toContain('El carro no está disponible para cargarse');
    expect(campo('carro').value).toBe('C-001');
    expect(el.querySelector('[role="status"]')).toBeNull();
  });

  it('avisa si el carro no existe', async () => {
    await crear(throwError(() => new CarroNoExiste('C-999')));
    escribir('carro', 'C-999');
    escribir('contenedor', '100123');
    await enviar();

    expect(el.querySelector('[role="alert"]')?.textContent).toContain('No existe un carro con el número C-999');
  });

  it('quita el aviso de éxito anterior al intentar de nuevo', async () => {
    await crear();
    escribir('carro', 'C-001');
    escribir('contenedor', '100123');
    await enviar();
    expect(el.querySelector('[role="status"]')).not.toBeNull();

    await enviar(); // campos vacíos
    expect(el.querySelector('[role="status"]')).toBeNull();
  });
});
