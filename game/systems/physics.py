"""Funcoes de fisica testaveis sem depender do Pygame."""


def approach(current: float, target: float, amount: float) -> float:
    """Aproxima current de target sem ultrapassar o alvo."""
    if current < target:
        return min(current + amount, target)
    return max(current - amount, target)


def integrate(position: float, velocity: float, acceleration: float, dt: float) -> tuple[float, float]:
    """Euler semi-implicito: v(t+dt)=v+a*dt; p(t+dt)=p+v*dt."""
    velocity += acceleration * dt
    position += velocity * dt
    return position, velocity


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))

