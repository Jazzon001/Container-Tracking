import { Component, ElementRef, OnInit, afterNextRender, computed, inject, signal, viewChild } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { mensajeDeApi } from './api-error';
import { Carro } from './carro.model';
import { CarrosService } from './carros.service';
import { Operacion } from './operacion';
import { hace } from './tiempo';

/** Cuántos carros se muestran a la vez: con más, la búsqueda sirve para acotar. */
export const LIMITE_LISTA = 50;

@Component({
  selector: 'app-entrega',
  imports: [ReactiveFormsModule],
  template: `
    <h1>Recibir carro</h1>
    <p class="ayuda">
      Escanea o escribe el código del contenedor elemento del carro que regresa vacío.
    </p>

    <form (submit)="enviar($event)">
      <label>
        Contenedor elemento
        <input
          #contenedor
          name="contenedor"
          autocomplete="off"
          [formControl]="codigo"
        />
      </label>
      <button type="submit" [disabled]="operacion.enviando()">Recibir carro</button>

      @if (operacion.mensaje()) { <p role="status">{{ operacion.mensaje() }}</p> }
      @if (operacion.error()) { <p role="alert">{{ operacion.error() }}</p> }
    </form>

    <section class="por-carro" aria-labelledby="titulo-por-carro">
      <h2 id="titulo-por-carro">Liberar por carro</h2>
      <p class="ayuda">
        ¿No tienes el código a la mano? Busca el carro en la lista de los que están en tránsito y pulsa Liberar.
      </p>

      <label>
        Buscar carro
        <input
          type="search"
          name="buscar"
          autocomplete="off"
          autocapitalize="characters"
          #caja
          [value]="busqueda()"
          (input)="busqueda.set(caja.value)"
        />
      </label>

      @if (liberacion.mensaje()) { <p role="status">{{ liberacion.mensaje() }}</p> }
      @if (liberacion.error()) { <p role="alert">{{ liberacion.error() }}</p> }
      @if (errorLista()) { <p role="alert">{{ errorLista() }}</p> }

      @if (cargando()) {
        <p class="vacio">Cargando carros en tránsito…</p>
      } @else {
        <p class="detalle">
          {{ visibles().length }} de {{ enTransito().length }} carros en tránsito
          <button type="button" class="secundario" (click)="cargarLista()">Actualizar</button>
        </p>
        @if (visibles().length > limite) {
          <p class="detalle">Se muestran los primeros {{ limite }}; escribe el número del carro para acotar.</p>
        }
        <ul>
          @for (carro of mostrados(); track carro.id) {
            <li class="carro">
              <div>
                <strong>{{ carro.numero }}</strong>
                @if (carro.contenedor_elemento) { <small>Contenedor {{ carro.contenedor_elemento }}</small> }
                <small>En tránsito {{ hace(carro.estado_desde, ahora()) }}</small>
              </div>
              @if (confirmando() === carro.id) {
                <div class="confirmar">
                  <span>¿Liberar {{ carro.numero }}?</span>
                  <button type="button" [disabled]="liberacion.enviando()" (click)="liberar(carro)">Sí, liberar</button>
                  <button type="button" class="secundario" (click)="confirmando.set(null)">Cancelar</button>
                </div>
              } @else {
                <button type="button" [attr.aria-label]="'Liberar ' + carro.numero" (click)="confirmando.set(carro.id)">Liberar</button>
              }
            </li>
          } @empty {
            <li class="vacio">No hay carros en tránsito para mostrar</li>
          }
        </ul>
      }
    </section>
  `,
  styles: `
    .ayuda { margin: 0 0 1rem; color: var(--color-suave); }
    .por-carro { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--color-borde); }
    h2 { margin: 0 0 0.5rem; font-size: 1.125rem; }
    .detalle { display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem; margin: 0 0 0.5rem; color: var(--color-suave); }
    ul { margin: 0.5rem 0 0; padding: 0; list-style: none; }
    .carro {
      display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.75rem;
      padding: 0.75rem 1rem; margin-bottom: 0.5rem;
      background: var(--color-superficie); border: 1px solid var(--color-borde); border-radius: var(--radio);
    }
    .carro small { display: block; color: var(--color-suave); }
    .confirmar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; }
    .vacio { padding: 1.5rem 0; text-align: center; color: var(--color-suave); }
  `,
})
export class EntregaComponent implements OnInit {
  private readonly carros = inject(CarrosService);
  private readonly campoContenedor = viewChild.required<ElementRef<HTMLInputElement>>('contenedor');

  readonly limite = LIMITE_LISTA;
  readonly hace = hace;
  readonly operacion = new Operacion();
  /** El resultado de liberar desde la lista, aparte del de escribir el contenedor. */
  readonly liberacion = new Operacion();
  // Control reactivo: al vaciarlo, el campo se limpia en el acto (ver CargaComponent).
  readonly codigo = new FormControl('', { nonNullable: true });

  readonly enTransito = signal<Carro[]>([]);
  readonly busqueda = signal('');
  readonly cargando = signal(true);
  readonly errorLista = signal('');
  /** El carro que se está por liberar: pide una confirmación antes, porque no se puede deshacer. */
  readonly confirmando = signal<number | null>(null);
  /** Momento de la última consulta: de aquí sale el "hace cuánto" de cada carro. */
  readonly ahora = signal(Date.now());

  readonly visibles = computed(() => {
    const texto = this.busqueda().trim().toUpperCase();
    const lista = this.enTransito();
    return texto ? lista.filter((carro) => carro.numero.toUpperCase().includes(texto)) : lista;
  });
  readonly mostrados = computed(() => this.visibles().slice(0, LIMITE_LISTA));

  constructor() {
    // Listo para escanear apenas se abre la pantalla.
    afterNextRender(() => this.campoContenedor().nativeElement.focus());
  }

  ngOnInit(): void {
    this.cargarLista();
  }

  /** Con un solo campo, el Enter del lector envía el formulario por sí mismo. */
  enviar(evento: Event): void {
    evento.preventDefault();
    const codigo = this.codigo.value.trim();
    if (!codigo) {
      this.operacion.fallar('Escribe o escanea el código del contenedor elemento.');
      return;
    }

    this.operacion.ejecutar(
      this.carros.entregarPorContenedor(codigo),
      (carro) => `Carro ${carro.numero} recibido (contenedor ${codigo}): ya está disponible para POY`,
      'No se pudo recibir el carro',
      () => {
        this.codigo.reset();
        this.campoContenedor().nativeElement.focus();
        this.cargarLista();
      },
    );
  }

  /** Libera el carro elegido en la lista, sin escanear nada. */
  liberar(carro: Carro): void {
    this.liberacion.ejecutar(
      this.carros.entregar(carro.id),
      (liberado) => `Carro ${liberado.numero} liberado: ya está disponible para POY`,
      'No se pudo liberar el carro',
      () => {
        this.confirmando.set(null);
        this.cargarLista();
      },
    );
  }

  cargarLista(): void {
    this.carros.listarEnTransito().subscribe({
      next: (carros) => {
        this.enTransito.set(carros);
        this.ahora.set(Date.now());
        this.errorLista.set('');
        this.cargando.set(false);
      },
      error: (fallo) => {
        this.errorLista.set(mensajeDeApi(fallo, 'No se pudo cargar la lista de carros en tránsito'));
        this.cargando.set(false);
      },
    });
  }
}
