import { Component, ElementRef, afterNextRender, inject, signal, viewChild } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { mensajeDeApi } from './api-error';
import { CarrosService } from './carros.service';

@Component({
  selector: 'app-entrega',
  imports: [ReactiveFormsModule],
  template: `
    <h1>Recibir carro</h1>
    <p class="ayuda">Escanea o escribe el número del carro que regresa vacío.</p>

    <form (submit)="enviar($event)">
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
      <button type="submit" [disabled]="enviando()">Recibir carro</button>

      @if (mensaje()) { <p role="status">{{ mensaje() }}</p> }
      @if (error()) { <p role="alert">{{ error() }}</p> }
    </form>
  `,
  styles: `
    .ayuda { margin: 0 0 1rem; color: var(--color-suave); }
  `,
})
export class EntregaComponent {
  private readonly carros = inject(CarrosService);
  private readonly campoCarro = viewChild.required<ElementRef<HTMLInputElement>>('carro');

  // Control reactivo: al vaciarlo, el campo se limpia en el acto (ver CargaComponent).
  readonly numero = new FormControl('', { nonNullable: true });
  readonly mensaje = signal('');
  readonly error = signal('');
  readonly enviando = signal(false);

  constructor() {
    // Listo para escanear apenas se abre la pantalla.
    afterNextRender(() => this.campoCarro().nativeElement.focus());
  }

  /** Con un solo campo, el Enter del lector envía el formulario por sí mismo. */
  enviar(evento: Event): void {
    evento.preventDefault();
    const numero = this.numero.value.trim();
    this.mensaje.set('');
    if (!numero) {
      this.error.set('Escribe o escanea el número del carro.');
      return;
    }

    this.error.set('');
    this.enviando.set(true);
    this.carros.entregarPorNumero(numero).subscribe({
      next: (carro) => {
        this.mensaje.set(`Carro ${carro.numero} recibido: ya está disponible para POY`);
        this.numero.reset();
        this.enviando.set(false);
        this.campoCarro().nativeElement.focus();
      },
      error: (fallo) => {
        this.error.set(mensajeDeApi(fallo, 'No se pudo recibir el carro'));
        this.enviando.set(false);
      },
    });
  }
}
