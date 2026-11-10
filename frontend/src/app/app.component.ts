import { Component, inject } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  template: `
    @if (auth.autenticado()) {
      <header class="barra">
        <span class="marca">Container Tracking</span>
        <button type="button" class="secundario" (click)="salir()">Salir</button>
      </header>
    }
    <main><router-outlet /></main>
  `,
  styles: `
    .barra {
      position: sticky; top: 0; z-index: 1;
      display: flex; align-items: center; justify-content: space-between; gap: 1rem;
      padding: 0.5rem 1rem;
      background: var(--color-superficie); border-bottom: 1px solid var(--color-borde);
    }
    .marca { font-weight: 700; letter-spacing: 0.02em; }
    main { max-width: 40rem; margin: 0 auto; padding: 1rem; }
  `,
})
export class App {
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  salir(): void {
    this.auth.logout();
    this.router.navigateByUrl('/login');
  }
}
