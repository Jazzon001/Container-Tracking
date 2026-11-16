import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { App } from './app.component';
import { AuthService, Rol } from './auth.service';
import { Accion, PERMISOS } from './perfiles';

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
      puede: (accion: Accion) => rol !== null && PERMISOS[rol][accion],
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

  describe('navegación según el perfil', () => {
    const COMPLETO = ['Carros', 'Cargar', 'Recibir', 'Mantenimiento', 'Historial'];
    const SIN_CARGAR = ['Carros', 'Recibir', 'Mantenimiento', 'Historial'];

    it.each(['digitador_poy', 'digitador_dty', 'digitador_twt', 'poy', 'dty'] as Rol[])(
      'quien carga ve el menú completo: %s',
      async (rol) => {
        await crear(true, rol);
        expect(enlaces()).toEqual(COMPLETO);
      },
    );

    it.each(['intermedio_poy', 'empacador_poy', 'empacador_dty', 'twisting', 'empacador_twt'] as Rol[])(
      'quien libera no ve el menú Cargar: %s',
      async (rol) => {
        await crear(true, rol);
        expect(enlaces()).toEqual(SIN_CARGAR);
      },
    );

    it('el administrador ve todo, incluido el Reporte', async () => {
      await crear(true, 'admin');
      expect(enlaces()).toEqual([...COMPLETO, 'Reporte']);
    });

    it('nadie más ve el Reporte', async () => {
      for (const rol of ['digitador_poy', 'intermedio_poy', 'twisting', 'almacen'] as Rol[]) {
        TestBed.resetTestingModule();
        await crear(true, rol);
        expect(enlaces()).not.toContain('Reporte');
      }
    });

    it('Almacén (perfil anterior) ve Carros, Recibir e Historial', async () => {
      await crear(true, 'almacen');
      expect(enlaces()).toEqual(['Carros', 'Recibir', 'Historial']);
    });
  });
});
