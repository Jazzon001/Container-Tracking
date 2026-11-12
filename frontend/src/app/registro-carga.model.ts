/** Un viaje de un carro: desde que se carga hasta que Almacén lo recibe vacío. */
export interface RegistroCarga {
  id: number;
  carro_id: number;
  carro_numero: string;
  contenedor_elemento: string;
  cargada_en: string;
  /** Nulo mientras el carro sigue en tránsito. */
  recibida_en: string | null;
}
