import { Component, inject, signal } from '@angular/core';
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
      <h1>Iniciar sesión</h1>
      <label>Usuario <input name="username" [ngModel]="username()" (ngModelChange)="username.set($event)" autocomplete="username" /></label>
      <label>Contraseña <input name="password" type="password" [ngModel]="password()" (ngModelChange)="password.set($event)" autocomplete="current-password" /></label>
      <button type="submit">Entrar</button>
      @if (error()) { <p role="alert">{{ error() }}</p> }
      @if (iniciada()) { <p>Sesión iniciada</p> }
    </form>
  `,
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly username = signal('');
  readonly password = signal('');
  readonly error = signal('');
  readonly iniciada = signal(false);

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
