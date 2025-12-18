def key_class(cls: str) -> list[int]:
        """
        Return a list of piano key numbers (1-88) matching the given class string.

        Rules:
        - Lowercase are naturals: 'c d e f g a b'
        - Uppercase are sharps of that letter: 'C D F G A' -> C# D# F# G# A#
        - Example: key_class('a')  -> [all A naturals]
                   key_class('aA') -> [all A naturals and A# keys]
        Unsupported tokens (e.g., 'B' or 'E' as sharps) are ignored.
        """
        natural_pc = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}
        sharp_pc   = {'C': 1, 'D': 3, 'F': 6, 'G': 8, 'A': 10}

        pcs: set[int] = set()
        for ch in cls:
            if ch in natural_pc:
                pcs.add(natural_pc[ch])
            elif ch in sharp_pc:
                pcs.add(sharp_pc[ch])
            # ignore unsupported tokens

        result: list[int] = []
        for keynum in range(1, 89):
            midi = keynum + 20  # key 1 (A0) => MIDI 21
            if (midi % 12) in pcs:
                result.append(keynum)
        return result

if __name__ == '__main__':
    print("Testing key_class function:")
    print('All a and a# keys if we number the keys from 1 to 88 are: ', key_class('aA'))  # Example usage