import { Component, ElementRef, afterNextRender, computed, inject, signal, viewChild } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { Carro } from './carro.model';
import { CarrosService } from './carros.service';
import { MantenimientoService } from './mantenimiento.service';
import { Operacion } from './operacion';
import { hace } from './tiempo';

@Component({
  selector: 'app-mantenimiento',
  imports: [ReactiveFormsModule],
  template: `
    <h1>Mantenimiento</h1>
    <p class="ayuda">Escanea o escribe el número del carro que entra a mantenimiento.</p>

    <form (submit)="registrarEntrada($event)">
      <label>
        Carro
        <input
          #carro
          name="carro"
          autocomplete="off"
          autocapitalize="characters"
          [formControl]="numero"
        />
      </label>
      <button type="submit" [disabled]="operacion.enviando()">Registrar entrada</button>
    </form>

    @if (operacion.mensaje()) { <p role="status">{{ operacion.mensaje() }}</p> }
    @if (operacion.error()) { <p role="alert">{{ operacion.error() }}</p> }

    <h2>En mantenimiento ({{ enMantenimiento().length }})</h2>
    <ul>
      @for (carro of enMantenimiento(); track carro.id) {
        <li class="carro">
          <div>
            <strong>{{ carro.numero }}</strong>
            <small>Desde {{ hace(carro.estado_desde, ahora()) }}</small>
          </div>
          <button
            type="button"
            class="secundario"
            [disabled]="operacion.enviando()"
            (click)="registrarSalida(carro)"
          >
            Dar salida
          </button>
        </li>
      } @empty {
        <li class="vacio">No hay carros en mantenimiento</li>
      }
    </ul>
  `,
  styles: `
    .ayuda { margin: 0 0 1rem; color: var(--color-suave); }
    h2 { margin: 1.5rem 0 0.75rem; font-size: 1.125rem; }
    ul { margin: 0; padding: 0; list-style: none; }
    .carro {
      display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;
      padding: 0.75rem 1rem; margin-bottom: 0.5rem;
      background: var(--color-superficie); border: 1px solid var(--color-borde); border-radius: var(--radio);
    }
    .carro small { display: block; color: var(--color-suave); }
    .vacio { padding: 1rem 0; text-align: center; color: var(--color-suave); }
  `,
})
export class MantenimientoComponent {
  private readonly carros = inject(CarrosService);
  private readonly mantenimiento = inject(MantenimientoService);
  private readonly campoCarro = viewChild.required<ElementRef<HTMLInputElement>>('carro');

  readonly hace = hace;
  readonly operacion = new Operacion();
  // Control reactivo: al vaciarlo, el campo se limpia en el acto (ver CargaComponent).
  readonly numero = new FormControl('', { nonNullable: true });
  readonly lista = signal<Carro[]>([]);
  readonly ahora = signal(Date.now());

  /** Los que llevan más tiempo en mantenimiento, primero. */
  readonly enMantenimiento = computed(() =>
    this.lista()
      .filter((carro) => carro.estado === 'en_mantenimiento')
      .sort((a, b) => Date.parse(a.estado_desde) - Date.parse(b.estado_desde)),
  );

  constructor() {
    this.cargarLista();
    // Listo para escanear apenas se abre la pantalla.
    afterNextRender(() => this.campoCarro().nativeElement.focus());
  }

  registrarEntrada(evento: Event): void {
    evento.preventDefault();
    const numero = this.numero.value.trim();
    if (!numero) {
      this.operacion.fallar('Escribe o escanea el número del carro.');
      return;
    }

    this.operacion.ejecutar(
      this.mantenimiento.iniciarPorNumero(numero),
      () => `Carro ${numero} registrado en mantenimiento`,
      'No se pudo registrar la entrada a mantenimiento',
      () => {
        this.numero.reset();
        this.campoCarro().nativeElement.focus();
        this.cargarLista();
      },
    );
  }

  registrarSalida(carro: Carro): void {
    this.operacion.ejecutar(
      this.mantenimiento.finalizar(carro.id),
      () => `Carro ${carro.numero} salió de mantenimiento y está disponible`,
      'No se pudo registrar la salida de mantenimiento',
      () => this.cargarLista(),
    );
  }

  private cargarLista(): void {
    this.carros.listar().subscribe({
      next: (carros) => {
        this.lista.set(carros);
        this.ahora.set(Date.now());
      },
      error: () => this.operacion.fallar('No se pudo cargar la lista de carros'),
    });
  }
}
