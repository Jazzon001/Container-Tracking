import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { Carro } from './carro.model';
import { CarroNoExiste, CarrosService } from './carros.service';
import { EntregaComponent } from './entrega.component';

const DISPONIBLE: Carro = {
  id: 1,
  numero: 'C-001',
  tipo: 'poy',
  estado: 'disponible',
  contenedor_elemento: null,
  estado_desde: '2026-11-12T12:00:00Z',
};

describe('EntregaComponent', () => {
  let fixture: ComponentFixture<EntregaComponent>;
  let el: HTMLElement;
  let entregarPorNumero: ReturnType<typeof vi.fn>;

  async function crear(respuesta: unknown = of(DISPONIBLE)) {
    entregarPorNumero = vi.fn().mockReturnValue(respuesta);
    await TestBed.configureTestingModule({
      imports: [EntregaComponent],
      providers: [{ provide: CarrosService, useValue: { entregarPorNumero } }],
    }).compileComponents();
    fixture = TestBed.createComponent(EntregaComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    el = fixture.nativeElement;
  }

  const campo = () => el.querySelector<HTMLInputElement>('input[name="carro"]')!;

  function escribir(valor: string) {
    campo().value = valor;
    campo().dispatchEvent(new Event('input'));
  }

  async function enviar() {
    el.querySelector<HTMLFormElement>('form')!.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
    await fixture.whenStable();
  }

  it('abre con el cursor en el campo del carro, listo para escanear', async () => {
    await crear();
    expect(document.activeElement).toBe(campo());
  });

  it('recibe el carro con el número escrito, sin espacios sobrantes', async () => {
    await crear();
    escribir('  C-001 ');
    await enviar();

    expect(entregarPorNumero).toHaveBeenCalledWith('C-001');
  });

  it('confirma la recepción, limpia el campo y vuelve a él', async () => {
    await crear();
    escribir('C-001');
    await enviar();

    expect(el.querySelector('[role="status"]')?.textContent).toContain('Carro C-001 recibido');
    expect(campo().value).toBe('');
    expect(document.activeElement).toBe(campo());
  });

  it('pide un número si el campo está vacío', async () => {
    await crear();
    await enviar();

    expect(entregarPorNumero).not.toHaveBeenCalled();
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('Escribe o escanea');
  });

  it('muestra el mensaje de la API si el carro no está en tránsito', async () => {
    const fallo = { status: 409, error: { detail: 'El carro no está en tránsito' } };
    await crear(throwError(() => fallo));
    escribir('C-001');
    await enviar();

    expect(el.querySelector('[role="alert"]')?.textContent).toContain('El carro no está en tránsito');
    expect(el.querySelector('[role="status"]')).toBeNull();
  });

  it('avisa si el carro no existe', async () => {
    await crear(throwError(() => new CarroNoExiste('C-999')));
    escribir('C-999');
    await enviar();

    expect(el.querySelector('[role="alert"]')?.textContent).toContain('No existe un carro con el número C-999');
  });
});
