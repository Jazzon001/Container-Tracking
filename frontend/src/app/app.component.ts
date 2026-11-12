import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from './auth.service';
import { ConexionService } from './conexion.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    @if (auth.autenticado()) {
      <header class="barra">
        <span class="marca">Container Tracking</span>
        <nav aria-label="Principal">
          <a routerLink="/carros" routerLinkActive="activa">Carros</a>
          @if (auth.puede('poy')) { <a routerLink="/carga" routerLinkActive="activa">Cargar</a> }
          @if (auth.puede('almacen')) { <a routerLink="/entrega" routerLinkActive="activa">Recibir</a> }
          @if (auth.puede('poy', 'dty')) { <a routerLink="/mantenimiento" routerLinkActive="activa">Mantenimiento</a> }
          <a routerLink="/historial" routerLinkActive="activa">Historial</a>
        </nav>
        <button type="button" class="secundario" (click)="salir()">Salir</button>
      </header>
    }
    @if (!conexion.enLinea()) {
      <p class="sin-conexion" role="status">
        Sin conexión: verás los últimos datos guardados y no podrás registrar operaciones hasta recuperarla.
      </p>
    }
    <main><router-outlet /></main>
  `,
  styles: `
    .barra {
      position: sticky; top: 0; z-index: 1;
      display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.25rem 1rem;
      padding: 0.5rem 1rem;
      background: var(--color-superficie); border-bottom: 1px solid var(--color-borde);
    }
    .marca { font-weight: 700; letter-spacing: 0.02em; }
    nav { display: flex; flex-wrap: wrap; gap: 0.25rem; }
    nav a {
      display: inline-flex; align-items: center; min-height: 2.75rem; padding: 0 0.75rem;
      color: var(--color-texto); text-decoration: none; font-weight: 500;
      border-bottom: 3px solid transparent;
    }
    nav a.activa { border-bottom-color: var(--color-primario); font-weight: 700; }
    @media (max-width: 30rem) { nav { order: 3; width: 100%; } }
    main { max-width: 40rem; margin: 0 auto; padding: 1rem; }
    .sin-conexion {
      margin: 0; padding: 0.5rem 1rem; text-align: center; font-weight: 500;
      color: var(--en-mantenimiento-texto); background: var(--en-mantenimiento-fondo);
    }
  `,
})
export class App {
  protected readonly auth = inject(AuthService);
  protected readonly conexion = inject(ConexionService);
  private readonly router = inject(Router);

  salir(): void {
    this.auth.logout();
    this.router.navigateByUrl('/login');
  }
}
