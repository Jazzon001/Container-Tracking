import { Component, OnInit, inject, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { mensajeDeApi } from './api-error';
import { HistorialService, LIMITE_HISTORIAL } from './historial.service';
import { RegistroCarga } from './registro-carga.model';
import { duracion } from './tiempo';

@Component({
  selector: 'app-historial',
  imports: [ReactiveFormsModule],
  template: `
    <h1>Historial de cargas</h1>
    <p class="ayuda">Cada viaje de un carro: qué contenedor elemento llevaba y cuánto tardó en volver.</p>

    <form (submit)="buscar($event)">
      <label>
        Carro
        <input name="numero" autocomplete="off" autocapitalize="characters" [formControl]="numero" />
      </label>
      <label>
        Contenedor elemento
        <input name="contenedor" autocomplete="off" [formControl]="contenedor" />
      </label>
      <button type="submit">Buscar</button>
    </form>

    @if (error()) { <p role="alert">{{ error() }}</p> }

    @if (cargando()) {
      <p class="vacio">Cargando historial…</p>
    } @else {
      <p class="detalle">
        {{ registros().length }} {{ registros().length === 1 ? 'viaje' : 'viajes' }}
        @if (registros().length === limite) { (los {{ limite }} más recientes; usa la búsqueda para acotar) }
      </p>
      <ul>
        @for (registro of registros(); track registro.id) {
          <li class="registro">
            <div>
              <strong>{{ registro.carro_numero }}</strong>
              <span class="contenedor">Contenedor {{ registro.contenedor_elemento }}</span>
              <small>Cargado: {{ fecha(registro.cargada_en) }}</small>
              <small>
                @if (registro.recibida_en) { Recibido: {{ fecha(registro.recibida_en) }} }
                @else { Aún en tránsito }
              </small>
            </div>
            <span class="insignia" [attr.data-estado]="registro.recibida_en ? 'disponible' : 'en_transito'">
              {{ duracion(registro.cargada_en, registro.recibida_en, ahora()) }}
            </span>
          </li>
        } @empty {
          <li class="vacio">No hay viajes para mostrar</li>
        }
      </ul>
    }
  `,
  styles: `
    .ayuda { margin: 0 0 1rem; color: var(--color-suave); }
    form { max-width: none; margin: 0 0 1rem; }
    .detalle { margin: 0 0 0.5rem; color: var(--color-suave); }
    ul { margin: 0; padding: 0; list-style: none; }
    .registro {
      display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;
      padding: 0.75rem 1rem; margin-bottom: 0.5rem;
      background: var(--color-superficie); border: 1px solid var(--color-borde); border-radius: var(--radio);
    }
    .registro small { display: block; color: var(--color-suave); }
    .contenedor { margin-left: 0.5rem; font-size: 0.8125rem; font-weight: 600; color: var(--color-suave); }
    .insignia {
      padding: 0.125rem 0.75rem; font-size: 0.875rem; font-weight: 600; white-space: nowrap;
      color: var(--estado-texto); background: var(--estado-fondo); border-radius: 999px;
    }
    .vacio { padding: 1.5rem 0; text-align: center; color: var(--color-suave); }
  `,
})
export class HistorialComponent implements OnInit {
  private readonly historial = inject(HistorialService);

  readonly limite = LIMITE_HISTORIAL;
  readonly duracion = duracion;
  readonly numero = new FormControl('', { nonNullable: true });
  readonly contenedor = new FormControl('', { nonNullable: true });
  readonly registros = signal<RegistroCarga[]>([]);
  readonly cargando = signal(true);
  readonly error = signal('');
  /** Momento de la última consulta: sirve para medir los viajes que siguen en curso. */
  readonly ahora = signal(Date.now());

  ngOnInit(): void {
    this.consultar();
  }

  buscar(evento: Event): void {
    evento.preventDefault();
    this.consultar();
  }

  /** Fecha y hora en la zona horaria de quien mira la pantalla (la API las entrega en UTC). */
  fecha(iso: string): string {
    return new Date(iso).toLocaleString('es', { dateStyle: 'short', timeStyle: 'short' });
  }

  private consultar(): void {
    this.historial
      .listar({ numero: this.numero.value.trim(), contenedor: this.contenedor.value.trim() })
      .subscribe({
        next: (registros) => {
          this.registros.set(registros);
          this.ahora.set(Date.now());
          this.error.set('');
          this.cargando.set(false);
        },
        error: (fallo) => {
          this.error.set(mensajeDeApi(fallo, 'No se pudo cargar el historial'));
          this.cargando.set(false);
        },
      });
  }
}
