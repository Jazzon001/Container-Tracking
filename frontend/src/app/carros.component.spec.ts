import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { AuthService } from './auth.service';
import { Carro } from './carro.model';
import { CarrosComponent } from './carros.component';
import { CarrosService } from './carros.service';

const CARROS: Carro[] = [
  { id: 1, numero: 'C-001', estado: 'disponible', contenedor_elemento: null },
  { id: 2, numero: 'C-002', estado: 'en_transito', contenedor_elemento: '100123' },
];

describe('CarrosComponent', () => {
  let fixture: ComponentFixture<CarrosComponent>;
  let el: HTMLElement;
  let listar: ReturnType<typeof vi.fn>;
  let logout: ReturnType<typeof vi.fn>;
  let navegar: ReturnType<typeof vi.fn>;

  async function crear(respuesta: unknown) {
    listar = vi.fn().mockReturnValue(respuesta);
    logout = vi.fn();
    navegar = vi.fn();
    await TestBed.configureTestingModule({
      imports: [CarrosComponent],
      providers: [
        { provide: CarrosService, useValue: { listar } },
        { provide: AuthService, useValue: { logout } },
        { provide: Router, useValue: { navigateByUrl: navegar } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(CarrosComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    el = fixture.nativeElement;
  }

  it('muestra los carros con su estado', async () => {
    await crear(of(CARROS));
    expect(el.textContent).toContain('C-001');
    expect(el.textContent).toContain('En tránsito');
    expect(el.textContent).toContain('2 carros');
  });

  it('muestra el contenedor elemento solo en los carros que lo tienen', async () => {
    await crear(of(CARROS));
    expect(el.textContent).toContain('Contenedor 100123');
    expect(el.querySelectorAll('small').length).toBe(1);
  });

  it('avisa cuando no hay carros', async () => {
    await crear(of([]));
    expect(el.textContent).toContain('No hay carros para mostrar');
  });

  it('muestra un error si la API falla', async () => {
    await crear(throwError(() => ({ status: 500 })));
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('No se pudieron cargar los carros');
  });

  it('vuelve a consultar con el estado elegido', async () => {
    await crear(of(CARROS));
    const select = el.querySelector<HTMLSelectElement>('select')!;
    select.value = 'disponible';
    select.dispatchEvent(new Event('change'));

    expect(listar).toHaveBeenLastCalledWith('disponible');
  });

  it('al elegir "Todos" consulta sin filtro', async () => {
    await crear(of(CARROS));
    const select = el.querySelector<HTMLSelectElement>('select')!;
    select.value = '';
    select.dispatchEvent(new Event('change'));

    expect(listar).toHaveBeenLastCalledWith(undefined);
  });

  it('cierra la sesión y vuelve al login al pulsar Salir', async () => {
    await crear(of(CARROS));
    el.querySelector<HTMLButtonElement>('header button')!.click();

    expect(logout).toHaveBeenCalled();
    expect(navegar).toHaveBeenCalledWith('/login');
  });
});
