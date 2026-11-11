/**
 * Convierte un fallo al llamar a la API en un texto para el usuario.
 * La API ya responde en español ("El carro no está disponible para cargarse"),
 * así que se muestra su mensaje tal cual cuando existe.
 */
export function mensajeDeApi(error: unknown, porDefecto: string): string {
  if (error instanceof Error) return error.message;
  const fallo = error as { status?: number; error?: { detail?: unknown } } | null;
  if (fallo?.status === 0) return 'No se pudo conectar con el servidor. Revisa que la API esté en marcha.';
  const detalle = fallo?.error?.detail;
  return typeof detalle === 'string' ? detalle : porDefecto;
}
