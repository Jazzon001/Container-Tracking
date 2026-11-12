"""Genera el logo de la aplicación en todos los tamaños que necesita una PWA.

Uso (necesita Pillow: pip install Pillow), desde la carpeta frontend:
    python tools/generar-iconos.py

Produce, dentro de public/:
    icons/icon-<tamaño>.png          íconos normales (esquinas redondeadas)
    icons/maskable-icon-<tamaño>.png íconos "maskable" (a sangre, para que Android los recorte)
    icons/apple-touch-icon.png       ícono para iOS (sin transparencia)
    icons/og-image.png               imagen al compartir el enlace (Open Graph)
    favicon.ico

El dibujo es propio (un carro de carga) y se hace con formas simples, sin recursos externos.
Los archivos generados se versionan: este script solo hace falta si se cambia el diseño.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PUBLIC = Path(__file__).resolve().parents[1] / "public"
ICONOS = PUBLIC / "icons"

AZUL = (29, 78, 216)  # #1d4ed8, el color primario de la aplicación
AZUL_OSCURO = (30, 58, 138)  # #1e3a8a
BLANCO = (255, 255, 255)
AMPLIACION = 4  # se dibuja en grande y se reduce: los bordes quedan suaves


def dibujar_carro(dibujo: ImageDraw.ImageDraw, x0: float, y0: float, lado: float, fondo) -> None:
    """Dibuja el carro dentro del cuadrado que empieza en (x0, y0) y mide `lado`."""

    def p(x: float, y: float) -> tuple[float, float]:
        return x0 + x * lado, y0 + y * lado

    def linea(a, b, ancho, color):
        dibujo.line([p(*a), p(*b)], fill=color, width=round(ancho * lado))
        for punto in (a, b):  # puntas redondeadas
            cx, cy = p(*punto)
            r = ancho * lado / 2
            dibujo.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    # Cesta con sus divisiones
    dibujo.rounded_rectangle([*p(0.02, 0.14), *p(0.84, 0.62)], radius=0.07 * lado, fill=BLANCO)
    for x in (0.2, 0.4, 0.6):
        linea((x, 0.2), (x, 0.56), 0.035, fondo)
    # Manillar
    linea((0.84, 0.24), (0.98, 0.04), 0.07, BLANCO)
    # Patas y ruedas
    linea((0.16, 0.62), (0.2, 0.8), 0.045, BLANCO)
    linea((0.7, 0.62), (0.66, 0.8), 0.045, BLANCO)
    for cx in (0.2, 0.66):
        x, y = p(cx, 0.86)
        r = 0.1 * lado
        dibujo.ellipse([x - r, y - r, x + r, y + r], fill=BLANCO)
        r2 = 0.04 * lado
        dibujo.ellipse([x - r2, y - r2, x + r2, y + r2], fill=fondo)


def icono(tamano: int, maskable: bool = False, redondeado: bool = True) -> Image.Image:
    grande = tamano * AMPLIACION
    imagen = Image.new("RGBA", (grande, grande), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(imagen)
    if maskable or not redondeado:
        dibujo.rectangle([0, 0, grande, grande], fill=AZUL)
    else:
        dibujo.rounded_rectangle([0, 0, grande - 1, grande - 1], radius=grande * 0.22, fill=AZUL)
    # En los maskable, el dibujo debe caber en el círculo central del 80 %.
    proporcion = 0.52 if maskable else 0.62
    lado = grande * proporcion
    dibujar_carro(dibujo, (grande - lado) / 2, (grande - lado) / 2 + grande * 0.01, lado, AZUL)
    return imagen.resize((tamano, tamano), Image.LANCZOS)


def tipografia(nombre: str, tamano: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for ruta in (f"C:/Windows/Fonts/{nombre}.ttf", f"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(ruta, tamano)
        except OSError:
            continue
    return ImageFont.load_default()


def imagen_para_compartir() -> Image.Image:
    ancho, alto = 1200, 630
    imagen = Image.new("RGB", (ancho, alto), AZUL)
    dibujo = ImageDraw.Draw(imagen)
    for y in range(alto):  # degradado vertical
        mezcla = y / alto
        color = tuple(round(a + (b - a) * mezcla) for a, b in zip(AZUL, AZUL_OSCURO))
        dibujo.line([(0, y), (ancho, y)], fill=color)
    imagen.paste(icono(320, redondeado=True), (110, 155), icono(320, redondeado=True))
    # El título debe caber en los 700 px de la derecha, con margen.
    dibujo.text((470, 200), "Container Tracking", font=tipografia("segoeuib", 68), fill=BLANCO)
    dibujo.text((474, 295), "Control de carros en tiempo real", font=tipografia("segoeui", 40), fill=(219, 234, 254))
    dibujo.text((474, 370), "POY  ·  DTY  ·  Twisting", font=tipografia("segoeui", 32), fill=(191, 219, 254))
    return imagen


def main() -> None:
    ICONOS.mkdir(parents=True, exist_ok=True)
    for tamano in (72, 96, 128, 144, 152, 192, 384, 512):
        icono(tamano).save(ICONOS / f"icon-{tamano}x{tamano}.png", optimize=True)
    for tamano in (192, 512):
        icono(tamano, maskable=True).save(ICONOS / f"maskable-icon-{tamano}x{tamano}.png", optimize=True)
    # iOS pone su propio recorte y no admite transparencia.
    icono(180, maskable=True).convert("RGB").save(ICONOS / "apple-touch-icon.png", optimize=True)
    imagen_para_compartir().save(ICONOS / "og-image.png", optimize=True)
    icono(256).save(PUBLIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"Íconos generados en {PUBLIC}")


if __name__ == "__main__":
    main()
