const MINUTO = 60_000;
const HORA = 60 * MINUTO;
const DIA = 24 * HORA;

/**
 * Describe cuánto tiempo pasó desde una fecha, en lenguaje corriente:
 * "hace instantes", "hace 25 min", "hace 3 h 10 min", "hace 2 d 4 h".
 * Solo muestra las dos unidades más grandes: para decidir basta con eso.
 */
export function hace(fechaIso: string, ahora: number): string {
  // Si el reloj de la computadora va un poco atrasado, nunca se muestra un tiempo negativo.
  const transcurrido = Math.max(0, ahora - Date.parse(fechaIso));

  if (transcurrido < MINUTO) return 'hace instantes';
  if (transcurrido < HORA) return `hace ${Math.floor(transcurrido / MINUTO)} min`;

  if (transcurrido < DIA) {
    const horas = Math.floor(transcurrido / HORA);
    const minutos = Math.floor((transcurrido % HORA) / MINUTO);
    return minutos > 0 ? `hace ${horas} h ${minutos} min` : `hace ${horas} h`;
  }

  const dias = Math.floor(transcurrido / DIA);
  const horas = Math.floor((transcurrido % DIA) / HORA);
  return horas > 0 ? `hace ${dias} d ${horas} h` : `hace ${dias} d`;
}
