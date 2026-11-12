import { Component, ElementRef, afterNextRender, inject, viewChild } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { CarrosService } from './carros.service';
import { Operacion } from './operacion';

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
  `,
  styles: `
    .ayuda { margin: 0 0 1rem; color: var(--color-suave); }
  `,
})
export class EntregaComponent {
  private readonly carros = inject(CarrosService);
  private readonly campoContenedor = viewChild.required<ElementRef<HTMLInputElement>>('contenedor');

  readonly operacion = new Operacion();
  // Control reactivo: al vaciarlo, el campo se limpia en el acto (ver CargaComponent).
  readonly codigo = new FormControl('', { nonNullable: true });

  constructor() {
    // Listo para escanear apenas se abre la pantalla.
    afterNextRender(() => this.campoContenedor().nativeElement.focus());
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
      },
    );
  }
}
