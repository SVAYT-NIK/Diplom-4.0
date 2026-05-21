// UploadZone component for Excel file upload
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadExcel } from '../services/api';
import type { UploadResponse } from '../services/types';

interface UploadZoneProps {
  onUploadSuccess: (response: UploadResponse) => void;
  onError: (error: string) => void;
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onUploadSuccess, onError }) => {
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    
    // Validate file type
    const validTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
    ];
    
    if (!validTypes.includes(file.type) && !file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      onError('Пожалуйста, загрузите файл Excel (.xlsx или .xls)');
      return;
    }

    setUploading(true);

    try {
      const response = await uploadExcel(file);
      onUploadSuccess(response);
    } catch (error) {
      console.error('Upload error:', error);
      onError(error instanceof Error ? error.message : 'Ошибка при загрузке файла');
    } finally {
      setUploading(false);
    }
  }, [onUploadSuccess, onError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: false,
    disabled: uploading,
  });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
        ${isDragActive 
          ? 'border-blue-500 bg-blue-50' 
          : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'}
        ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />
      
      {uploading ? (
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
          <p className="text-gray-600">Загрузка и обработка файла...</p>
        </div>
      ) : isDragActive ? (
        <div className="flex flex-col items-center gap-3">
          <svg className="w-12 h-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className="text-blue-600 font-medium">Отпустите файл здесь...</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <div>
            <p className="text-gray-700 font-medium">Перетащите Excel файл сюда</p>
            <p className="text-gray-500 text-sm mt-1">или нажмите для выбора файла</p>
          </div>
          <p className="text-gray-400 text-xs mt-2">Поддерживаются форматы .xlsx и .xls</p>
        </div>
      )}
    </div>
  );
};

export default UploadZone;
