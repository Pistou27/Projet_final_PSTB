"""
Utilitaires pour mesurer le temps d'exécution
"""

import time
import functools
from contextlib import contextmanager
from typing import Iterator, Callable, Any

def timer(func: Callable) -> Callable:
    """Décorateur pour mesurer le temps d'exécution d'une fonction"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed_time = time.time() - start_time
            # Import ici pour éviter la circularité
            try:
                from .logger import Logger
                Logger.info(f"⏱️  {func.__name__}: {elapsed_time:.2f}s")
            except ImportError:
                print(f"⏱️  {func.__name__}: {elapsed_time:.2f}s")
    return wrapper

@contextmanager
def timer_context() -> Iterator[float]:
    """Context manager pour mesurer le temps d'exécution"""
    start_time = time.time()
    elapsed_time = 0.0
    
    def get_elapsed():
        nonlocal elapsed_time
        elapsed_time = time.time() - start_time
        return elapsed_time
    
    try:
        yield get_elapsed
    finally:
        elapsed_time = time.time() - start_time

class Timer:
    """Classe pour mesurer les temps d'exécution"""
    
    def __init__(self):
        self.start_time = None
        self.elapsed_time = 0.0
    
    def start(self):
        """Démarre le timer"""
        self.start_time = time.time()
    
    def stop(self) -> float:
        """Arrête le timer et retourne le temps écoulé"""
        if self.start_time is None:
            return 0.0
        
        self.elapsed_time = time.time() - self.start_time
        return self.elapsed_time
    
    def get_elapsed(self) -> float:
        """Retourne le temps écoulé depuis le start"""
        if self.start_time is None:
            return 0.0
        
        return time.time() - self.start_time
    
    @contextmanager
    def measure(self) -> Iterator[float]:
        """Context manager pour mesurer automatiquement"""
        self.start()
        try:
            yield self.get_elapsed
        finally:
            self.stop()
