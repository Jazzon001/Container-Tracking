import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Subject, of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { Carro } from './carro.model';
import { CarrosComponent } from './carros.component';
import { CarrosService } from './carros.service';

const CARROS: Carro[] = [
  { id: 1, numero: 'C-001', estado: 'disponible', contenedor_elemento: null },
  { id: 2, numero: 'C-002', estado: 'en_transito', contenedor_elemento: '100123' },
  { id: 3, numero: 'C-003', estado: 'disponible', contenedor_elemento: null },
];

describe('CarrosComponent', () => {
  let fixture: ComponentFixture<CarrosComponent>;
  let el: HTMLElement;

  async function crear(respuesta: unknown) {
    await TestBed.configureTestingModule({
      imports: [CarrosComponent],
      providers: [{ provide: CarrosService, useValue: { listar: vi.fn().mockReturnValue(respuesta) } }],
    }).compileComponents();
    fixture = TestBed.createComponent(CarrosComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    el = fixture.nativeElement;
  }

  const tarjeta = (estado: string) => el.querySelector<HTMLButtonElement>(`.tarjeta[data-estado="${estado}"]`)!;
  const filas = () => el.querySelectorAll('.carro');

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
    expect(el.querySelectorAll('small').length).toBe(1);
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

  it('filtra al tocar la tarjeta de un estado', async () => {
    await crear(of(CARROS));
    tarjeta('en_transito').click();
    fixture.detectChanges();

    expect(filas().length).toBe(1);
    expect(filas()[0].textContent).toContain('C-002');
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

  it('quita el filtro con el botón "Mostrar todos"', async () => {
    await crear(of(CARROS));
    tarjeta('disponible').click();
    fixture.detectChanges();
    el.querySelector<HTMLButtonElement>('.detalle button')!.click();
    fixture.detectChanges();

    expect(filas().length).toBe(3);
  });
});
