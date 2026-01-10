return role_vector, {
    "entropy": entropy,
    "entropy_mean": self.entropy_window.mean(),
    "active_constraints": list(self.active_constraints),
    "identity_pressure": self.identity_pressure
}
