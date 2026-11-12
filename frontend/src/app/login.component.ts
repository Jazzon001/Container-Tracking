import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';

/** Cada tipo de fallo se explica distinto: así el usuario sabe qué corregir. */
function mensajeDeError(status: number): string {
  if (status === 401) return 'Usuario o contraseña incorrectos';
  if (status === 0) return 'No se pudo conectar con el servidor. Revisa que la API esté en marcha.';
  return 'El servidor tuvo un problema. Intenta de nuevo.';
}

@Component({
  selector: 'app-login',
  imports: [FormsModule],
  template: `
    <form (submit)="entrar($event)">
      <p class="marca">Container Tracking</p>
      <h1>Iniciar sesión</h1>
      <p class="ayuda">Ingresa con tu usuario del sistema.</p>
      <label>Usuario <input name="username" [ngModel]="username()" (ngModelChange)="username.set($event)" autocomplete="username" /></label>
      <label>Contraseña <input name="password" type="password" [ngModel]="password()" (ngModelChange)="password.set($event)" autocomplete="current-password" /></label>
      <button type="submit">Entrar</button>
      @if (error()) { <p role="alert">{{ error() }}</p> }
      @if (iniciada()) { <p>Sesión iniciada</p> }
    </form>
  `,
  styles: `
    .marca {
      margin: 0 0 0.5rem; font-size: 0.875rem; font-weight: 700;
      letter-spacing: 0.08em; text-transform: uppercase; color: var(--color-primario);
    }
    h1 { margin-bottom: 0.25rem; }
    .ayuda { margin: 0 0 1.5rem; color: var(--color-suave); }
  `,
})
export class LoginComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly username = signal('');
  readonly password = signal('');
  readonly error = signal('');
  readonly iniciada = signal(false);

  ngOnInit(): void {
    // Quien ya tiene sesión no necesita ver el formulario (por ejemplo, si el servidor lo
    // mandó aquí porque le faltaba la cookie de sesión).
    if (this.auth.autenticado()) this.router.navigateByUrl('/carros');
  }

  entrar(evento: Event): void {
    evento.preventDefault();
    if (!this.username() || !this.password()) return;
    this.auth.login(this.username(), this.password()).subscribe({
      next: () => {
        this.error.set('');
        this.iniciada.set(true);
        this.router.navigateByUrl('/carros');
      },
      error: (fallo: { status: number }) => {
        this.iniciada.set(false);
        this.error.set(mensajeDeError(fallo.status));
      },
    });
  }
}
