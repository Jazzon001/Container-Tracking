import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { LoginComponent } from './login.component';
import { AuthService } from './auth.service';

describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let el: HTMLElement;
  let auth: jasmine.SpyObj<AuthService>;

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
    auth = jasmine.createSpyObj<AuthService>('AuthService', ['login']);
    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [{ provide: AuthService, useValue: auth }],
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
    auth.login.and.returnValue(of({ access_token: 'abc', token_type: 'bearer' }));
    escribir('input[name="username"]', 'poy1');
    escribir('input[name="password"]', 'secreta');
    enviar();
    expect(auth.login).toHaveBeenCalledWith('poy1', 'secreta');
    expect(el.textContent).toContain('Sesión iniciada');
  });

  it('muestra un error si las credenciales son incorrectas', () => {
    auth.login.and.returnValue(throwError(() => ({ status: 401 })));
    escribir('input[name="username"]', 'poy1');
    escribir('input[name="password"]', 'mala');
    enviar();
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('Usuario o contraseña incorrectos');
  });

  it('no envía si faltan datos', () => {
    enviar();
    expect(auth.login).not.toHaveBeenCalled();
  });
});
