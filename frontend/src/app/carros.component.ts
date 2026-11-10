import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Carro, ESTADOS, ETIQUETAS_ESTADO, EstadoCarro } from './carro.model';
import { CarrosService } from './carros.service';

@Component({
  selector: 'app-carros',
  template: `
    <h1>Carros</h1>

    @if (error()) { <p role="alert">{{ error() }}</p> }

    <section class="resumen" aria-label="Resumen por estado">
      @for (estado of estados; track estado) {
        <button
          type="button"
          class="tarjeta"
          [attr.data-estado]="estado"
          [attr.aria-pressed]="filtro() === estado"
          (click)="elegir(estado)"
        >
          <span class="cantidad">{{ conteos()[estado] }}</span>
          <span>{{ etiquetas[estado] }}</span>
        </button>
      }
    </section>

    <p class="detalle">
      @if (filtro(); as estado) {
        Mostrando {{ visibles().length }} de {{ carros().length }} carros ({{ etiquetas[estado] }})
        <button type="button" class="secundario" (click)="quitarFiltro()">Mostrar todos</button>
      } @else {
        {{ carros().length }} carros en total
      }
    </p>

    @if (cargando()) {
      <p class="vacio">Cargando carros…</p>
    } @else {
      <ul>
        @for (carro of visibles(); track carro.id) {
          <li class="carro">
            <div>
              <strong>{{ carro.numero }}</strong>
              @if (carro.contenedor_elemento) {
                <small>Contenedor {{ carro.contenedor_elemento }}</small>
              }
            </div>
            <span class="insignia" [attr.data-estado]="carro.estado">{{ etiquetas[carro.estado] }}</span>
          </li>
        } @empty {
          <li class="vacio">No hay carros para mostrar</li>
        }
      </ul>
    }
  `,
  styles: `
    .resumen { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; margin-bottom: 1rem; }
    .tarjeta {
      display: flex; flex-direction: column; align-items: center; gap: 0.25rem;
      padding: 0.75rem 0.5rem; font-weight: 500; text-align: center;
      color: var(--color-texto); background: var(--color-superficie);
      border: 2px solid var(--color-borde);
    }
    .tarjeta[aria-pressed='true'] { border-color: var(--estado-texto); background: var(--estado-fondo); }
    .cantidad { font-size: 1.75rem; font-weight: 700; line-height: 1; color: var(--estado-texto); }
    .detalle { display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem; color: var(--color-suave); }
    ul { margin: 0; padding: 0; list-style: none; }
    .carro {
      display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;
      padding: 0.75rem 1rem; margin-bottom: 0.5rem;
      background: var(--color-superficie); border: 1px solid var(--color-borde); border-radius: var(--radio);
    }
    .carro small { display: block; color: var(--color-suave); }
    .insignia {
      padding: 0.125rem 0.75rem; font-size: 0.875rem; font-weight: 600; white-space: nowrap;
      color: var(--estado-texto); background: var(--estado-fondo); border-radius: 999px;
    }
    .vacio { padding: 1.5rem 0; text-align: center; color: var(--color-suave); }
  `,
})
export class CarrosComponent implements OnInit {
  private readonly carrosService = inject(CarrosService);

  readonly estados = ESTADOS;
  readonly etiquetas = ETIQUETAS_ESTADO;
  readonly carros = signal<Carro[]>([]);
  readonly filtro = signal<EstadoCarro | null>(null);
  readonly cargando = signal(true);
  readonly error = signal('');

  readonly conteos = computed(() => {
    const total = Object.fromEntries(ESTADOS.map((estado) => [estado, 0])) as Record<EstadoCarro, number>;
    for (const carro of this.carros()) total[carro.estado]++;
    return total;
  });

  readonly visibles = computed(() => {
    const estado = this.filtro();
    return estado ? this.carros().filter((carro) => carro.estado === estado) : this.carros();
  });

  ngOnInit(): void {
    this.carrosService.listar().subscribe({
      next: (carros) => {
        this.carros.set(carros);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudieron cargar los carros');
        this.cargando.set(false);
      },
    });
  }

  /** Tocar la tarjeta de un estado filtra; tocarla otra vez quita el filtro. */
  elegir(estado: EstadoCarro): void {
    this.filtro.update((actual) => (actual === estado ? null : estado));
  }

  quitarFiltro(): void {
    this.filtro.set(null);
  }
}
