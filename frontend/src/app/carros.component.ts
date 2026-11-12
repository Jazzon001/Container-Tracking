import { Component, InjectionToken, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subject, catchError, interval, map, of, switchMap } from 'rxjs';
import { Carro, ESTADOS, ETIQUETAS_ESTADO, EstadoCarro } from './carro.model';
import { CarrosService } from './carros.service';
import { hace } from './tiempo';

/** Cada cuánto se vuelve a consultar la lista. Es un token para poder acortarlo en las pruebas. */
export const INTERVALO_ACTUALIZACION_MS = new InjectionToken<number>('INTERVALO_ACTUALIZACION_MS', {
  providedIn: 'root',
  factory: () => 30_000,
});

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

    <p class="detalle">
      Actualizado a las {{ horaActualizacion() }}
      <button type="button" class="secundario" (click)="cargar()">Actualizar</button>
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
              <small class="tiempo">Desde {{ hace(carro.estado_desde, ahora()) }}</small>
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
    .detalle { display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem; margin: 0 0 0.5rem; color: var(--color-suave); }
    ul { margin: 0.5rem 0 0; padding: 0; list-style: none; }
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
  private readonly recarga = new Subject<void>();

  readonly estados = ESTADOS;
  readonly etiquetas = ETIQUETAS_ESTADO;
  readonly hace = hace;
  readonly carros = signal<Carro[]>([]);
  readonly filtro = signal<EstadoCarro | null>(null);
  readonly cargando = signal(true);
  readonly error = signal('');
  /** Momento de la última consulta: de aquí se calcula el "hace cuánto" de cada carro. */
  readonly ahora = signal(Date.now());

  readonly horaActualizacion = computed(() =>
    new Date(this.ahora()).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' }),
  );

  readonly conteos = computed(() => {
    const total = Object.fromEntries(ESTADOS.map((estado) => [estado, 0])) as Record<EstadoCarro, number>;
    for (const carro of this.carros()) total[carro.estado]++;
    return total;
  });

  readonly visibles = computed(() => {
    const estado = this.filtro();
    if (!estado) return this.carros();
    const lista = this.carros().filter((carro) => carro.estado === estado);
    // En tránsito: primero los que llevan más tiempo, que son los que hay que ir a buscar.
    return estado === 'en_transito'
      ? [...lista].sort((a, b) => Date.parse(a.estado_desde) - Date.parse(b.estado_desde))
      : lista;
  });

  constructor() {
    // switchMap descarta una consulta lenta si ya salió otra más nueva: nunca se pisa
    // una lista reciente con una vieja. Un fallo no detiene las consultas siguientes.
    this.recarga
      .pipe(
        switchMap(() =>
          this.carrosService.listar().pipe(
            map((carros) => ({ carros })),
            catchError(() => of(null)),
          ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((resultado) => {
        if (resultado) {
          this.carros.set(resultado.carros);
          this.ahora.set(Date.now());
          this.error.set('');
        } else {
          this.error.set('No se pudieron cargar los carros');
        }
        this.cargando.set(false);
      });

    interval(inject(INTERVALO_ACTUALIZACION_MS))
      .pipe(takeUntilDestroyed())
      .subscribe(() => this.cargar());
  }

  ngOnInit(): void {
    this.cargar();
  }

  cargar(): void {
    this.recarga.next();
  }

  /** Tocar la tarjeta de un estado filtra; tocarla otra vez quita el filtro. */
  elegir(estado: EstadoCarro): void {
    this.filtro.update((actual) => (actual === estado ? null : estado));
  }

  quitarFiltro(): void {
    this.filtro.set(null);
  }
}
