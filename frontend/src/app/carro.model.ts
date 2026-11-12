export type EstadoCarro = 'disponible' | 'en_transito' | 'en_mantenimiento';

export interface Carro {
  id: number;
  numero: string;
  estado: EstadoCarro;
  contenedor_elemento: string | null;
  /** Fecha y hora (UTC) en que el carro pasó a su estado actual. */
  estado_desde: string;
}

/** Texto que ve el usuario para cada estado. Sus claves son la lista de estados. */
export const ETIQUETAS_ESTADO: Record<EstadoCarro, string> = {
  disponible: 'Disponible',
  en_transito: 'En tránsito',
  en_mantenimiento: 'En mantenimiento',
};

export const ESTADOS = Object.keys(ETIQUETAS_ESTADO) as EstadoCarro[];
