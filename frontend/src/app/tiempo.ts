const MINUTO = 60_000;
const HORA = 60 * MINUTO;
const DIA = 24 * HORA;

/**
 * Una duración en lenguaje corriente, con las dos unidades más grandes: "25 min",
 * "3 h 10 min", "2 d 4 h". Para decidir basta con eso. Vacía si es menos de un minuto.
 */
function describir(milisegundos: number): string {
  if (milisegundos < MINUTO) return '';
  if (milisegundos < HORA) return `${Math.floor(milisegundos / MINUTO)} min`;

  if (milisegundos < DIA) {
    const horas = Math.floor(milisegundos / HORA);
    const minutos = Math.floor((milisegundos % HORA) / MINUTO);
    return minutos > 0 ? `${horas} h ${minutos} min` : `${horas} h`;
  }

  const dias = Math.floor(milisegundos / DIA);
  const horas = Math.floor((milisegundos % DIA) / HORA);
  return horas > 0 ? `${dias} d ${horas} h` : `${dias} d`;
}

/** Cuánto pasó desde una fecha: "hace instantes", "hace 25 min", "hace 2 d 4 h". */
export function hace(fechaIso: string, ahora: number): string {
  // Si el reloj de la computadora va un poco atrasado, nunca se muestra un tiempo negativo.
  const texto = describir(Math.max(0, ahora - Date.parse(fechaIso)));
  return texto ? `hace ${texto}` : 'hace instantes';
}

/**
 * Cuánto duró algo entre dos fechas: "25 min", "3 h 10 min", "2 d 4 h".
 * Si todavía no termina (`hastaIso` es nulo), cuenta hasta `ahora`.
 */
export function duracion(desdeIso: string, hastaIso: string | null, ahora: number): string {
  const fin = hastaIso === null ? ahora : Date.parse(hastaIso);
  return describir(Math.max(0, fin - Date.parse(desdeIso))) || 'menos de 1 min';
}
