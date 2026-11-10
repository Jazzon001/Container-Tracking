import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { vi } from 'vitest';
import { App } from './app.component';
import { AuthService } from './auth.service';

describe('App', () => {
  let fixture: ComponentFixture<App>;
  let el: HTMLElement;
  let logout: ReturnType<typeof vi.fn>;
  let navegar: ReturnType<typeof vi.fn>;

  async function crear(autenticado: boolean) {
    logout = vi.fn();
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: { autenticado: signal(autenticado), logout } },
      ],
    }).compileComponents();
    navegar = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true) as never;
    fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    el = fixture.nativeElement;
  }

  it('tiene un punto de salida para las rutas', async () => {
    await crear(false);
    expect(el.querySelector('router-outlet')).toBeTruthy();
  });

  it('muestra la barra con la marca cuando hay sesión', async () => {
    await crear(true);
    expect(el.querySelector('.barra')?.textContent).toContain('Container Tracking');
  });

  it('no muestra la barra sin sesión (por ejemplo, en el login)', async () => {
    await crear(false);
    expect(el.querySelector('.barra')).toBeNull();
  });

  it('cierra la sesión y vuelve al login al pulsar Salir', async () => {
    await crear(true);
    el.querySelector<HTMLButtonElement>('.barra button')!.click();

    expect(logout).toHaveBeenCalled();
    expect(navegar).toHaveBeenCalledWith('/login');
  });
});
