import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';
import { Carro, ESTADOS, ETIQUETAS_ESTADO, EstadoCarro } from './carro.model';
import { CarrosService } from './carros.service';

@Component({
  selector: 'app-carros',
  template: `
    <header>
      <h1>Carros</h1>
      <button type="button" (click)="salir()">Salir</button>
    </header>

    <label>
      Estado
      <select name="estado" #selector [value]="filtro()" (change)="cambiarFiltro(selector.value)">
        <option value="">Todos</option>
        @for (estado of estados; track estado) {
          <option [value]="estado">{{ etiquetas[estado] }}</option>
        }
      </select>
    </label>

    @if (error()) { <p role="alert">{{ error() }}</p> }

    <p>{{ carros().length }} carros</p>
    <ul>
      @for (carro of carros(); track carro.id) {
        <li>
          <strong>{{ carro.numero }}</strong>
          <span>{{ etiquetas[carro.estado] }}</span>
          @if (carro.contenedor_elemento) { <small>Contenedor {{ carro.contenedor_elemento }}</small> }
        </li>
      } @empty {
        <li>No hay carros para mostrar</li>
      }
    </ul>
  `,
  styles: `
    :host { display: block; max-width: 40rem; margin: 0 auto; padding: 1rem; }
    header { display: flex; justify-content: space-between; align-items: center; }
    ul { list-style: none; padding: 0; }
    li { display: flex; flex-wrap: wrap; gap: 0.5rem; padding: 0.75rem 0; border-bottom: 1px solid #ddd; }
    li span { margin-left: auto; }
    select, button { font: inherit; min-height: 2.75rem; }
  `,
})
export class CarrosComponent implements OnInit {
  private readonly carrosService = inject(CarrosService);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly estados = ESTADOS;
  readonly etiquetas = ETIQUETAS_ESTADO;
  readonly carros = signal<Carro[]>([]);
  readonly filtro = signal<EstadoCarro | ''>('');
  readonly error = signal('');

  ngOnInit(): void {
    this.cargar();
  }

  cambiarFiltro(valor: string): void {
    this.filtro.set(valor as EstadoCarro | '');
    this.cargar();
  }

  salir(): void {
    this.auth.logout();
    this.router.navigateByUrl('/login');
  }

  private cargar(): void {
    this.carrosService.listar(this.filtro() || undefined).subscribe({
      next: (carros) => {
        this.carros.set(carros);
        this.error.set('');
      },
      error: () => this.error.set('No se pudieron cargar los carros'),
    });
  }
}
