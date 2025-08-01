// AudioUtils.ts
export class AudioUtils {
    static async createPCM16Data(audioBuffer: AudioBuffer): Promise<ArrayBuffer> {
        const numChannels = 1; // Mono
        const sampleRate = 16000; // Target sample rate
        const format = 1; // PCM
        const bitDepth = 16;

        // Resample if needed
        let samples = audioBuffer.getChannelData(0);
        if (audioBuffer.sampleRate !== sampleRate) {
            samples = await this.resampleAudio(samples, audioBuffer.sampleRate, sampleRate);
        }

        const dataLength = samples.length * (bitDepth / 8);
        const headerLength = 44;
        const totalLength = headerLength + dataLength;

        const buffer = new ArrayBuffer(totalLength);
        const view = new DataView(buffer);

        // Write WAV header
        this.writeString(view, 0, 'RIFF');
        view.setUint32(4, totalLength - 8, true);
        this.writeString(view, 8, 'WAVE');
        this.writeString(view, 12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, format, true);
        view.setUint16(22, numChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * numChannels * (bitDepth / 8), true);
        view.setUint16(32, numChannels * (bitDepth / 8), true);
        view.setUint16(34, bitDepth, true);
        this.writeString(view, 36, 'data');
        view.setUint32(40, dataLength, true);

        // Write audio data
        this.floatTo16BitPCM(view, 44, samples);

        return buffer;
    }

    static writeString(view: DataView, offset: number, string: string): void {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }

    static floatTo16BitPCM(view: DataView, offset: number, input: Float32Array): void {
        for (let i = 0; i < input.length; i++, offset += 2) {
            const s = Math.max(-1, Math.min(1, input[i]));
            view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
        }
    }

    static async resampleAudio(
        audioData: Float32Array,
        originalSampleRate: number,
        targetSampleRate: number
    ): Promise<Float32Array> {
        const originalLength = audioData.length;
        const ratio = targetSampleRate / originalSampleRate;
        const newLength = Math.round(originalLength * ratio);
        const result = new Float32Array(newLength);

        for (let i = 0; i < newLength; i++) {
            const position = i / ratio;
            const index = Math.floor(position);
            const fraction = position - index;

            if (index + 1 < originalLength) {
                result[i] = audioData[index] * (1 - fraction) + audioData[index + 1] * fraction;
            } else {
                result[i] = audioData[index];
            }
        }

        return result;
    }

}

export default AudioUtils;
