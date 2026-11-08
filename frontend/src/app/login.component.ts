import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from './auth.service';

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
  readonly username = signal('');
  readonly password = signal('');
  readonly error = signal('');
  readonly iniciada = signal(false);

  entrar(evento: Event): void {
    evento.preventDefault();
    if (!this.username() || !this.password()) return;
    this.auth.login(this.username(), this.password()).subscribe({
      next: () => { this.error.set(''); this.iniciada.set(true); },
      error: () => { this.iniciada.set(false); this.error.set('Usuario o contraseña incorrectos'); },
    });
  }
}
