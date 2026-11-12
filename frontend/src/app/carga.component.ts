import { Component, ElementRef, afterNextRender, inject, viewChild } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { CarrosService } from './carros.service';
import { Operacion } from './operacion';

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
      <button type="submit" [disabled]="operacion.enviando()">Cargar carro</button>

      @if (operacion.mensaje()) { <p role="status">{{ operacion.mensaje() }}</p> }
      @if (operacion.error()) { <p role="alert">{{ operacion.error() }}</p> }
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

  readonly operacion = new Operacion();
  // Controles reactivos: al vaciarlos, el campo se limpia en el acto. Con un lector de
  // código de barras (que escribe muy rápido) no se puede depender de que la pantalla
  // se refresque entre el escaneo y el envío.
  readonly numero = new FormControl('', { nonNullable: true });
  readonly codigo = new FormControl('', { nonNullable: true });

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
    if (!numero || !codigo) {
      this.operacion.fallar('Escribe o escanea el carro y el contenedor elemento.');
      return;
    }

    this.operacion.ejecutar(
      this.carros.cargarPorNumero(numero, codigo),
      (carro) => `Carro ${carro.numero} cargado con el contenedor ${carro.contenedor_elemento}`,
      'No se pudo cargar el carro',
      () => {
        this.numero.reset();
        this.codigo.reset();
        this.campoCarro().nativeElement.focus();
      },
    );
  }
}
