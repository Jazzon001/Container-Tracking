export type EstadoCarro = 'disponible' | 'en_transito' | 'en_mantenimiento';

/** Proceso al que pertenece el carro (en NOW: C01, C02 y C03). */
export type TipoCarro = 'poy' | 'dty' | 'twisting';

export interface Carro {
  id: number;
  numero: string;
  tipo: TipoCarro;
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

/** Texto que ve el usuario para cada tipo. Sus claves son la lista de tipos. */
export const ETIQUETAS_TIPO: Record<TipoCarro, string> = {
  poy: 'POY',
  dty: 'DTY',
  twisting: 'Twisting',
};

export const TIPOS = Object.keys(ETIQUETAS_TIPO) as TipoCarro[];
