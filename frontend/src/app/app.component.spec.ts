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

  describe('aviso de falta de conexión', () => {
    const aviso = () => el.querySelector('.sin-conexion');

    afterEach(() => window.dispatchEvent(new Event('online')));

    it('no muestra el aviso si hay conexión', async () => {
      await crear(true, 'poy');
      expect(aviso()).toBeNull();
    });

    it('muestra el aviso cuando se pierde la conexión, también en el login', async () => {
      await crear(false);
      window.dispatchEvent(new Event('offline'));
      fixture.detectChanges();

      expect(aviso()?.textContent).toContain('Sin conexión');
    });

    it('quita el aviso cuando se recupera', async () => {
      await crear(true, 'poy');
      window.dispatchEvent(new Event('offline'));
      fixture.detectChanges();
      window.dispatchEvent(new Event('online'));
      fixture.detectChanges();

      expect(aviso()).toBeNull();
    });
  });

  describe('navegación según el rol', () => {
    it('POY ve Carros, Cargar, Mantenimiento e Historial', async () => {
      await crear(true, 'poy');
      expect(enlaces()).toEqual(['Carros', 'Cargar', 'Mantenimiento', 'Historial']);
    });

    it('Almacén ve Carros, Recibir e Historial', async () => {
      await crear(true, 'almacen');
      expect(enlaces()).toEqual(['Carros', 'Recibir', 'Historial']);
    });

    it('DTY ve Carros, Mantenimiento e Historial', async () => {
      await crear(true, 'dty');
      expect(enlaces()).toEqual(['Carros', 'Mantenimiento', 'Historial']);
    });

    it('Twisting solo consulta: Carros e Historial', async () => {
      await crear(true, 'twisting');
      expect(enlaces()).toEqual(['Carros', 'Historial']);
    });

    it('el administrador ve todo', async () => {
      await crear(true, 'admin');
      expect(enlaces()).toEqual(['Carros', 'Cargar', 'Recibir', 'Mantenimiento', 'Historial']);
    });
  });
});
