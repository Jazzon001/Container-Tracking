import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { LoginComponent } from './login.component';
import { AuthService } from './auth.service';

describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let el: HTMLElement;
  let auth: { login: ReturnType<typeof vi.fn> };
  let navegar: ReturnType<typeof vi.fn>;

  function escribir(selector: string, valor: string) {
    const input = el.querySelector<HTMLInputElement>(selector)!;
    input.value = valor;
    input.dispatchEvent(new Event('input'));
  }

  function enviar() {
    el.querySelector<HTMLFormElement>('form')!.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
  }

  beforeEach(async () => {
    auth = { login: vi.fn() };
    navegar = vi.fn();
    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        { provide: AuthService, useValue: auth },
        { provide: Router, useValue: { navigateByUrl: navegar } },
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(LoginComponent);
    fixture.detectChanges();
    el = fixture.nativeElement;
  });

  it('muestra campos de usuario y contraseña', () => {
    expect(el.querySelector('input[name="username"]')).toBeTruthy();
    expect(el.querySelector('input[name="password"][type="password"]')).toBeTruthy();
  });

  it('envía las credenciales escritas al servicio', () => {
    auth.login.mockReturnValue(of({ access_token: 'abc', token_type: 'bearer' }));
    escribir('input[name="username"]', 'poy1');
    escribir('input[name="password"]', 'secreta');
    enviar();
    expect(auth.login).toHaveBeenCalledWith('poy1', 'secreta');
    expect(el.textContent).toContain('Sesión iniciada');
  });

  it('va a la pantalla de carros al iniciar sesión', () => {
    auth.login.mockReturnValue(of({ access_token: 'abc', token_type: 'bearer' }));
    escribir('input[name="username"]', 'poy1');
    escribir('input[name="password"]', 'secreta');
    enviar();
    expect(navegar).toHaveBeenCalledWith('/carros');
  });

  it('muestra un error si las credenciales son incorrectas', () => {
    auth.login.mockReturnValue(throwError(() => ({ status: 401 })));
    escribir('input[name="username"]', 'poy1');
    escribir('input[name="password"]', 'mala');
    enviar();
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('Usuario o contraseña incorrectos');
    expect(navegar).not.toHaveBeenCalled();
  });

  it('avisa que no hay conexión si la API no responde', () => {
    auth.login.mockReturnValue(throwError(() => ({ status: 0 })));
    escribir('input[name="username"]', 'poy1');
    escribir('input[name="password"]', 'secreta');
    enviar();
    const mensaje = el.querySelector('[role="alert"]')?.textContent;
    expect(mensaje).toContain('No se pudo conectar');
    expect(mensaje).not.toContain('incorrectos');
  });

  it('avisa de un problema del servidor sin culpar a las credenciales', () => {
    auth.login.mockReturnValue(throwError(() => ({ status: 500 })));
    escribir('input[name="username"]', 'poy1');
    escribir('input[name="password"]', 'secreta');
    enviar();
    const mensaje = el.querySelector('[role="alert"]')?.textContent;
    expect(mensaje).toContain('problema');
    expect(mensaje).not.toContain('incorrectos');
  });

  it('no envía si faltan datos', () => {
    enviar();
    expect(auth.login).not.toHaveBeenCalled();
  });
});
