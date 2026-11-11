import { Component, ElementRef, afterNextRender, inject, signal, viewChild } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { mensajeDeApi } from './api-error';
import { CarrosService } from './carros.service';

@Component({
  selector: 'app-carga',
  imports: [ReactiveFormsModule],
  template: `
    <h1>Cargar carro</h1>
    <p class="ayuda">Escanea o escribe el número del carro y el código del contenedor elemento.</p>

    <form (submit)="enviar($event)">
      <label>
        Carro
        <input
          #carro
          name="carro"
          autocomplete="off"
          autocapitalize="characters"
          [formControl]="numero"
          (keydown.enter)="pasarAlContenedor($event)"
        />
      </label>
      <label>
        Contenedor elemento
        <input
          #contenedor
          name="contenedor"
          autocomplete="off"
          [formControl]="codigo"
        />
      </label>
      <button type="submit" [disabled]="enviando()">Cargar carro</button>

      @if (mensaje()) { <p role="status">{{ mensaje() }}</p> }
      @if (error()) { <p role="alert">{{ error() }}</p> }
    </form>
  `,
  styles: `
    .ayuda { margin: 0 0 1rem; color: var(--color-suave); }
  `,
})
export class CargaComponent {
  private readonly carros = inject(CarrosService);
  private readonly campoCarro = viewChild.required<ElementRef<HTMLInputElement>>('carro');
  private readonly campoContenedor = viewChild.required<ElementRef<HTMLInputElement>>('contenedor');

  // Controles reactivos: al vaciarlos, el campo se limpia en el acto. Con un lector de
  // código de barras (que escribe muy rápido) no se puede depender de que la pantalla
  // se refresque entre el escaneo y el envío.
  readonly numero = new FormControl('', { nonNullable: true });
  readonly codigo = new FormControl('', { nonNullable: true });
  readonly mensaje = signal('');
  readonly error = signal('');
  readonly enviando = signal(false);

  constructor() {
    // Listo para escanear apenas se abre la pantalla.
    afterNextRender(() => this.campoCarro().nativeElement.focus());
  }

  /** Los lectores de código de barras terminan con Enter: pasar al siguiente campo, sin enviar. */
  pasarAlContenedor(evento: Event): void {
    evento.preventDefault();
    this.campoContenedor().nativeElement.focus();
  }

  enviar(evento: Event): void {
    evento.preventDefault();
    const numero = this.numero.value.trim();
    const codigo = this.codigo.value.trim();
    this.mensaje.set('');
    if (!numero || !codigo) {
      this.error.set('Escribe o escanea el carro y el contenedor elemento.');
      return;
    }

    this.error.set('');
    this.enviando.set(true);
    this.carros.cargarPorNumero(numero, codigo).subscribe({
      next: (carro) => {
        this.mensaje.set(`Carro ${carro.numero} cargado con el contenedor ${carro.contenedor_elemento}`);
        this.numero.reset();
        this.codigo.reset();
        this.enviando.set(false);
        this.campoCarro().nativeElement.focus();
      },
      error: (fallo) => {
        this.error.set(mensajeDeApi(fallo, 'No se pudo cargar el carro'));
        this.enviando.set(false);
      },
    });
  }
}
