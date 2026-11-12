import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { Carro } from './carro.model';
import { CarrosService, ContenedorNoEncontrado } from './carros.service';
import { EntregaComponent } from './entrega.component';

const DISPONIBLE: Carro = {
  id: 1,
  numero: 'P001A',
  tipo: 'poy',
  estado: 'disponible',
  contenedor_elemento: null,
  estado_desde: '2026-11-12T12:00:00Z',
};

describe('EntregaComponent', () => {
  let fixture: ComponentFixture<EntregaComponent>;
  let el: HTMLElement;
  let entregarPorContenedor: ReturnType<typeof vi.fn>;

  async function crear(respuesta: unknown = of(DISPONIBLE)) {
    entregarPorContenedor = vi.fn().mockReturnValue(respuesta);
    await TestBed.configureTestingModule({
      imports: [EntregaComponent],
      providers: [{ provide: CarrosService, useValue: { entregarPorContenedor } }],
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

  it('pide solo el contenedor elemento, no el número del carro', async () => {
    await crear();
    expect(el.querySelectorAll('input').length).toBe(1);
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
});
