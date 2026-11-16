/** Una cifra clave del reporte, con su nombre ya redactado por la API. */
export interface Indicador {
  indicador: string;
  valor: number | string;
}

/** Una fila de una tabla de horas: cuántos viajes y las horas promedio y máxima. */
export interface FilaTabla {
  clave: string;
  viajes: number;
  promedio: number;
  maximo: number;
}

export interface TablaHoras {
  titulo: string;
  columna: string;
  filas: FilaTabla[];
}

/** Un lado (A o B) de un carro, con dónde se le ve según NOW y según este sistema. */
export interface FilaCarroReporte {
  carro_fisico: string;
  lado: string;
  carro: string;
  viajes: number;
  ultimo_contenedor: string;
  calidad: string;
  situacion: string;
  horas_en_situacion: number | null;
  horas_promedio_en_rcv: number | null;
  horas_promedio_en_wip: number | null;
  situacion_sistema: string;
  /** Cuántos de sus viajes tienen registro en este sistema. */
  viajes_en_sistema: number;
  horas_en_dty: number | null;
  /** Salió hacia DTY, se cargó en este sistema y todavía no se libera: las horas siguen corriendo. */
  dty_abierto: boolean;
  horas_promedio_en_dty: number | null;
}

export interface ReporteCarros {
  /** Hora local de la planta (la de NOW) del último movimiento del archivo. */
  corte: string;
  resumen: Indicador[];
  tablas: TablaHoras[];
  carros: FilaCarroReporte[];
}
