import os
import json
import boto3
import time
from typing import Dict, Optional
from botocore.exceptions import BotoCoreError, ClientError

class TTSPollyService:
    """
    Serviço simplificado para Text-to-Speech usando Amazon Polly
    Focado em performance e qualidade de voz natural
    """
    
    def __init__(self, region_name: str = 'us-east-1', output_dir: str = None):
        """
        Inicializa o serviço Polly
        
        Args:
            region_name (str): Região AWS para o serviço Polly
            output_dir (str): Diretório para salvar arquivos de áudio (padrão: /tmp)
        """
        try:
            self.polly_client = boto3.client('polly', region_name=region_name)
            self.output_dir = output_dir or "/tmp"
            
            # Configurações padrão para voz natural e rápida
            self.default_config = {
                'voice_id': 'Joanna',  # Voz feminina natural em inglês
                'output_format': 'mp3',
                'sample_rate': '24000',  # Alta qualidade
                'text_type': 'text',
                'language_code': 'en-US'
            }
            
            # Vozes recomendadas para inglês natural
            self.recommended_voices = {
                'female': ['Joanna', 'Kimberly', 'Salli', 'Kendra', 'Ivy'],
                'male': ['Matthew', 'Joey', 'Justin', 'Kevin'],
                'neural': ['Joanna', 'Matthew', 'Ivy', 'Justin', 'Kendra', 'Kimberly', 'Salli', 'Joey', 'Kevin']
            }
            
            # Garantir que o diretório de saída existe
            os.makedirs(self.output_dir, exist_ok=True)
            
        except Exception as e:
            raise Exception(f"Erro ao inicializar TTSPollyService: {e}")
    

    
    def text_to_speech(self, 
                      text: str, 
                      voice_id: str = None, 
                      output_format: str = 'mp3',
                      speed: str = 'medium',
                      use_neural: bool = True) -> Dict:
        """
        Converte texto para fala usando Amazon Polly
        
        Args:
            text (str): Texto para conversão
            voice_id (str): ID da voz (ex: 'Joanna')
            output_format (str): Formato de saída ('mp3', 'wav', 'ogg_vorbis')
            speed (str): Velocidade ('x-slow', 'slow', 'medium', 'fast', 'x-fast')
            use_neural (bool): Usar engine neural para melhor qualidade
            
        Returns:
            dict: Resultado da conversão
        """
        try:
            start_time = time.time()
            
            # Usar voz padrão se não especificada
            if not voice_id:
                voice_id = self.default_config['voice_id']
            
            # Processar texto básico (apenas limpar e limitar tamanho)
            processed_text = text.strip()
            if len(processed_text) > 3000:
                processed_text = processed_text[:2900] + "..."
            
            # Configurar parâmetros de síntese
            synthesis_params = {
                'Text': processed_text,
                'OutputFormat': output_format,
                'VoiceId': voice_id,
                'LanguageCode': self.default_config['language_code']
            }
            
            # Usar engine neural se disponível e solicitado
            if use_neural and voice_id in self.recommended_voices['neural']:
                synthesis_params['Engine'] = 'neural'
            else:
                synthesis_params['Engine'] = 'standard'
            
            # Adicionar configurações de velocidade usando SSML
            if speed != 'medium':
                ssml_text = f'<speak><prosody rate="{speed}">{processed_text}</prosody></speak>'
                synthesis_params['Text'] = ssml_text
                synthesis_params['TextType'] = 'ssml'
            
            # Adicionar taxa de amostragem para qualidade
            if output_format == 'mp3':
                synthesis_params['SampleRate'] = '24000'
            elif output_format == 'wav':
                synthesis_params['SampleRate'] = '22050'
            
            # Realizar síntese
            response = self.polly_client.synthesize_speech(**synthesis_params)
            
            # Gerar nome único para o arquivo
            timestamp = int(time.time() * 1000)
            filename = f"tts_audio_{timestamp}.{output_format}"
            file_path = os.path.join(self.output_dir, filename)
            
            # Salvar arquivo de áudio
            with open(file_path, 'wb') as audio_file:
                audio_file.write(response['AudioStream'].read())
            
            # Calcular métricas
            processing_time = time.time() - start_time
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            
            # Estimar duração do áudio (aproximada)
            # Velocidade média de fala: ~150-180 caracteres por segundo
            chars_per_second = 165  # Velocidade média
            estimated_duration = len(text) / chars_per_second
            
            result = {
                'success': True,
                'file_path': file_path,
                'filename': filename,
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size_mb, 3),
                'processing_time': round(processing_time, 2),
                'duration': round(estimated_duration, 2),  # em segundos
                'voice_id': voice_id,
                'output_format': output_format,
                'engine': synthesis_params.get('Engine', 'standard'),
                'text_length': len(text),
                'processed_text_length': len(processed_text)
            }
            
            return result
            
        except (BotoCoreError, ClientError) as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'aws_error'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'error_type': 'general_error'
            }
    
    def text_to_speech_streaming(self, text: str, voice_id: str = None) -> Dict:
        """
        Converte texto para fala usando streaming para textos longos
        
        Args:
            text (str): Texto para conversão
            voice_id (str): ID da voz
            
        Returns:
            dict: Resultado da conversão com streaming
        """
        try:
            if not voice_id:
                voice_id = self.default_config['voice_id']
            
            # Dividir texto em chunks para streaming
            chunks = self._split_text_for_streaming(text)
            
            timestamp = int(time.time() * 1000)
            filename = f"tts_streaming_{timestamp}.mp3"
            file_path = os.path.join(self.output_dir, filename)
            
            total_size = 0
            
            with open(file_path, 'wb') as output_file:
                for i, chunk in enumerate(chunks):
                    response = self.polly_client.synthesize_speech(
                        Text=chunk,
                        OutputFormat='mp3',
                        VoiceId=voice_id,
                        Engine='neural' if voice_id in self.recommended_voices['neural'] else 'standard'
                    )
                    
                    chunk_data = response['AudioStream'].read()
                    output_file.write(chunk_data)
                    total_size += len(chunk_data)
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': filename,
                'file_size_bytes': total_size,
                'file_size_mb': round(total_size / (1024 * 1024), 3),
                'chunks_processed': len(chunks),
                'voice_id': voice_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _split_text_for_streaming(self, text: str, max_length: int = 2500) -> list:
        """
        Divide texto em chunks para processamento streaming
        
        Args:
            text (str): Texto para dividir
            max_length (int): Tamanho máximo de cada chunk
            
        Returns:
            list: Lista de chunks de texto
        """
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def cleanup_temp_files(self, max_age_minutes: int = 60) -> int:
        """
        Remove arquivos temporários antigos
        
        Args:
            max_age_minutes (int): Idade máxima dos arquivos em minutos
            
        Returns:
            int: Número de arquivos removidos
        """
        try:
            removed_count = 0
            current_time = time.time()
            max_age_seconds = max_age_minutes * 60
            
            for filename in os.listdir(self.output_dir):
                if filename.startswith('tts_'):
                    file_path = os.path.join(self.output_dir, filename)
                    file_age = current_time - os.path.getctime(file_path)
                    
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        removed_count += 1
            
            return removed_count
            
        except Exception as e:
            return 0


# Função utilitária para uso direto
def quick_tts(text: str, voice: str = 'Joanna', speed: str = 'medium') -> str:
    """
    Função rápida para TTS simples
    
    Args:
        text (str): Texto para conversão
        voice (str): Voz a usar
        speed (str): Velocidade da fala
        
    Returns:
        str: Caminho do arquivo gerado ou None se erro
    """
    try:
        tts = TTSPollyService()
        result = tts.text_to_speech(text=text, voice_id=voice, speed=speed)
        
        if result['success']:
            return result['file_path']
        else:
            return None
            
    except Exception as e:
        return None


# Teste do serviço (apenas para desenvolvimento local)
if __name__ == "__main__":
    # Testar o serviço
    tts_service = TTSPollyService()
    
    # Teste de conversão
    test_text = "Hello! This is a test of our fast and natural text-to-speech system using Amazon Polly."
    
    result = tts_service.text_to_speech(
        text=test_text,
        voice_id='Joanna',
        speed='medium',
        use_neural=True
    )
    
    if result['success']:
        print(f"✅ TTS Test Success!")
        print(f"   File: {result['filename']}")
        print(f"   Size: {result['file_size_mb']} MB")
        print(f"   Duration: {result['duration']} seconds")
        print(f"   Processing Time: {result['processing_time']} seconds")
    else:
        print(f"❌ TTS Test Failed: {result['error']}")
