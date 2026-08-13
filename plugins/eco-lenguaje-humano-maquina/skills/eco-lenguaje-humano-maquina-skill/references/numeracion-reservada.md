# Numeración reservada

## Regla

Tratar los prefijos iguales o mayores que `50` como nombres gobernados. Cuando un prefijo recibe significado, conservar el mismo nombre y propósito en todos los niveles. No reutilizarlo para otra función.

Reservas vigentes:

| Prefijo | Nombre exacto | Propósito |
|---|---|---|
| `80` | `80_LENGUAJE_HUMANO_MAQUINA` | Derivados humanos y de máquina regenerables del proyecto o área propietaria |
| `90` | `90_HISTORICO` | Versiones superadas, archivo histórico o evidencia cerrada |
| `98` | `98_ENTRADA_GENERAL` | Ingreso temporal global pendiente de destino |
| `99` | `99_CONTROL` | Estado, reglas, manifiestos, eventos, validaciones y evidencias de control |

Mantener `50` a `79`, excepto `80`, sin asignar hasta aprobar una reserva canónica. Usar numeración inferior a `50` para contenido operativo ordinario.

No crear nombres como `80_OTRO_USO`, `90_ARCHIVO`, `90_GENERADOS`, `99_REPORTES` o `99_EVIDENCIAS`. Ubicar reportes, evidencias y generados dentro de una carpeta operativa inferior a `50` o como subcarpetas sin prefijo dentro de `99_CONTROL`.

Dentro de `80_LENGUAJE_HUMANO_MAQUINA`, usar `99_CONTROL` para controles generales o particulares. No crear `90_CONTROL_DOCUMENTO` ni `90_CONTROL_TECNICO`.
