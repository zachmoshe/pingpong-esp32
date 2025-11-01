# micropython_wav_writer.py
# 
# A utility class for MicroPython (v1.26+) devices to correctly construct and write 
# a standard 44-byte PCM WAV header alongside raw audio data.
#
# Usage: Use with a 'with' statement for automatic header finalization and closing.
#
# Requires: MicroPython with the 'struct' module enabled (standard).

import struct

class WAVWriter:
    """
    A class to handle writing raw PCM audio data into a complete WAV file.
    It reserves space for the header initially and writes the final header 
    upon calling close() or exiting a 'with' block.
    """
    
    def __init__(self, file_path, sample_rate, channels=1, bits_per_sample=16):
        """
        Initializes the WAV file writer. Opens the file and writes a placeholder 
        header.

        Args:
            file_path (str): The path to the output WAV file.
            sample_rate (int): Sample rate (Hz).
            channels (int): Number of audio channels (1=mono, 2=stereo).
            bits_per_sample (int): Bit depth (8, 16, 24, or 32).
        """
        
        self.file_path = file_path
        self.sample_rate = sample_rate
        self.channels = channels
        self.bits_per_sample = bits_per_sample
        self.data_size = 0
        
        # Calculate dependent fields for consistency
        self.block_align = channels * (bits_per_sample // 8)
        self.byte_rate = sample_rate * self.block_align
        
        # Open the file for binary writing
        self.f = open(self.file_path, 'wb')
        
        # Reserve 44 bytes for the header. The data will be filled in on close().
        # Writing data size 0 initially.
        self._write_header(final_data_size=0)
        
        print(f"WAVWriter initialized for '{file_path}'")
        print(f"Rate: {sample_rate}Hz, Channels: {channels}, Bit Depth: {bits_per_sample}")


    def _write_header(self, final_data_size):
        """Internal method to construct and write the 44-byte header."""

        # Seek to the beginning of the file to write/overwrite the header
        self.f.seek(0)

        # --- RIFF Chunk (12 bytes) ---
        chunk_size = 36 + final_data_size
        self.f.write(struct.pack('<4sI4s', b'RIFF', chunk_size, b'WAVE'))

        # --- 'fmt ' Sub-chunk (24 bytes) ---
        subchunk1_size = 16 
        audio_format = 1 # PCM (uncompressed)

        self.f.write(struct.pack('<4sIHHIIHH', 
                            b'fmt ',             # Subchunk 1 ID
                            subchunk1_size,       # Size of the rest of the fmt sub-chunk (16)
                            audio_format,         # Audio Format (1=PCM)
                            self.channels,        # Number of channels
                            self.sample_rate,     # Sample Rate
                            self.byte_rate,       # Byte Rate
                            self.block_align,     # Block Align
                            self.bits_per_sample))# Bits Per Sample

        # --- 'data' Sub-chunk (8 bytes) ---
        self.f.write(struct.pack('<4sI', b'data', final_data_size))
        
        # Seek back to the end of the file data to continue writing
        self.f.seek(44 + final_data_size)


    def write(self, data):
        """
        Writes a chunk of raw PCM audio data to the file and updates the size.
        
        Args:
            data (bytes or bytearray): The raw audio data chunk.
        """
        bytes_written = self.f.write(data)
        self.data_size += bytes_written


    def close(self):
        """
        Finalizes the WAV file by writing the correct total data size into the header 
        and closing the underlying file handle.
        """
        if self.f:
            print(f"\nClosing file. Finalizing header with data size: {self.data_size} bytes.")
            # Write the correct header
            self._write_header(self.data_size)
            # Close the file
            self.f.close()
            self.f = None
            print("WAV file complete.")


    # Context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Only finalize and close if no exception occurred during the block.
        if exc_type is None:
            self.close()
        else:
            print(f"Error occurred: {exc_value}. File closed without final header.")
            # If an error occurs, just close the file handle without rewriting the header
            if self.f:
                self.f.close()

