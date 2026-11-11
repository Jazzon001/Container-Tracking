import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { App } from './app.component';
import { AuthService, Rol } from './auth.service';

describe('App', () => {
  let fixture: ComponentFixture<App>;
  let el: HTMLElement;
  let logout: ReturnType<typeof vi.fn>;
  let navegar: ReturnType<typeof vi.fn>;

  async function crear(autenticado: boolean, rol: Rol | null = null) {
    logout = vi.fn();
    const auth = {
      autenticado: signal(autenticado),
      logout,
      // Igual que el servicio real: el administrador puede todo.
      puede: (...roles: Rol[]) => rol !== null && (rol === 'admin' || roles.includes(rol)),
    };
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([]), { provide: AuthService, useValue: auth }],
    }).compileComponents();
    navegar = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true) as never;
    fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    el = fixture.nativeElement;
  }

  const enlaces = () => Array.from(el.querySelectorAll('nav a')).map((a) => a.textContent?.trim());

  it('tiene un punto de salida para las rutas', async () => {
    await crear(false);
    expect(el.querySelector('router-outlet')).toBeTruthy();
  });

  it('muestra la barra con la marca cuando hay sesión', async () => {
    await crear(true, 'dty');
    expect(el.querySelector('.barra')?.textContent).toContain('Container Tracking');
  });

  it('no muestra la barra sin sesión (por ejemplo, en el login)', async () => {
    await crear(false);
    expect(el.querySelector('.barra')).toBeNull();
  });

  it('cierra la sesión y vuelve al login al pulsar Salir', async () => {
    await crear(true, 'poy');
    el.querySelector<HTMLButtonElement>('.barra button')!.click();

    expect(logout).toHaveBeenCalled();
    expect(navegar).toHaveBeenCalledWith('/login');
  });

  describe('navegación según el rol', () => {
    it('POY ve Carros y Cargar', async () => {
      await crear(true, 'poy');
      expect(enlaces()).toEqual(['Carros', 'Cargar']);
    });

    it('Almacén ve Carros y Recibir', async () => {
      await crear(true, 'almacen');
      expect(enlaces()).toEqual(['Carros', 'Recibir']);
    });

    it('DTY solo ve Carros', async () => {
      await crear(true, 'dty');
      expect(enlaces()).toEqual(['Carros']);
    });

    it('el administrador ve todo', async () => {
      await crear(true, 'admin');
      expect(enlaces()).toEqual(['Carros', 'Cargar', 'Recibir']);
    });
  });
});
