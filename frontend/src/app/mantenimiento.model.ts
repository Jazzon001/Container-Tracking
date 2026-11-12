/** Un paso de un carro por mantenimiento. Mientras `fecha_salida` es nula, sigue abierto. */
export interface Mantenimiento {
  id: number;
  carro_id: number;
  fecha_entrada: string;
  fecha_salida: string | null;
}
