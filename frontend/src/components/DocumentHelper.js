import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { FileText, UploadSimple, CheckCircle, XCircle, WarningCircle } from '@phosphor-icons/react';
import { toast } from 'sonner';

const DocumentHelper = ({ category, complaintId }) => {
  const { token } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  useEffect(() => {
    fetchRequiredDocuments();
    if (complaintId) {
      fetchUploadedDocuments();
    }
  }, [category]);

  const fetchRequiredDocuments = async () => {
    try {
      const response = await axios.post(
        `${API}/documents/suggest`,
        { category },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setDocuments(response.data.documents);
    } catch (error) {
      console.error('Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  };

  const fetchUploadedDocuments = async () => {
    try {
      const response = await axios.get(`${API}/documents/${complaintId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUploadedDocs(response.data);
    } catch (error) {
      console.error('Failed to fetch uploaded documents');
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Only PDF, JPG, and PNG files are allowed');
      return;
    }

    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('complaint_id', complaintId || 'temp');

      const response = await axios.post(`${API}/documents/upload`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      setUploadedDocs([...uploadedDocs, response.data]);
      toast.success('Document uploaded successfully');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const isDocumentUploaded = (docName) => {
    return uploadedDocs.some(doc => 
      doc.file_name.toLowerCase().includes(docName.toLowerCase().split(' ')[0])
    );
  };

  if (loading) {
    return (
      <div className="bg-white border border-[#E4E4E7] p-6 md:p-8">
        <div className="text-center text-[#52525B]">Loading document requirements...</div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-[#E4E4E7] p-6 md:p-8" data-testid="document-helper-section">
      <div className="mb-6">
        <h3 className="text-xl sm:text-2xl font-bold tracking-tight mb-2">Required Documents</h3>
        <p className="text-sm text-[#52525B]">
          Based on your complaint category, here are the documents you may need to attach.
        </p>
      </div>

      <div className="space-y-3 mb-6">
        {documents.map((doc, index) => {
          const uploaded = isDocumentUploaded(doc.name);
          return (
            <div
              key={index}
              className="flex items-start gap-4 p-4 border border-[#E4E4E7] hover:border-[#09090B] transition-colors"
              data-testid={`document-item-${index}`}
            >
              <div className="flex-shrink-0 mt-1">
                {uploaded ? (
                  <CheckCircle size={24} weight="bold" className="text-green-600" />
                ) : doc.required ? (
                  <WarningCircle size={24} weight="bold" className="text-[#E11D48]" />
                ) : (
                  <FileText size={24} weight="bold" className="text-[#52525B]" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="text-base font-bold tracking-tight text-[#09090B]">{doc.name}</h4>
                  {doc.required && (
                    <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#E11D48]">Required</span>
                  )}
                  {uploaded && (
                    <span className="text-xs font-bold uppercase tracking-[0.2em] text-green-600">Uploaded</span>
                  )}
                </div>
                <p className="text-sm text-[#52525B]">{doc.description}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Upload Section */}
      <div className="bg-[#F4F4F5] border border-[#E4E4E7] p-6">
        <label
          htmlFor="document-upload"
          data-testid="upload-document-button"
          className="w-full bg-transparent border-2 border-dashed border-[#09090B] hover:border-[#002FA7] hover:bg-white transition-all p-8 flex flex-col items-center justify-center cursor-pointer"
        >
          <UploadSimple size={48} weight="bold" className="text-[#09090B] mb-3" />
          <span className="text-base font-bold tracking-tight text-[#09090B] mb-2">
            {uploading ? 'Uploading...' : 'Click to Upload Document'}
          </span>
          <span className="text-xs text-[#52525B]">
            PDF, JPG, or PNG (Max 5MB)
          </span>
        </label>
        <input
          id="document-upload"
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={handleFileUpload}
          disabled={uploading}
          className="hidden"
          data-testid="file-input"
        />
      </div>

      {uploadedDocs.length > 0 && (
        <div className="mt-6">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-3">
            Uploaded Documents ({uploadedDocs.length})
          </div>
          <div className="space-y-2">
            {uploadedDocs.map((doc, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-green-50 border border-green-200"
                data-testid={`uploaded-doc-${index}`}
              >
                <div className="flex items-center gap-2">
                  <CheckCircle size={18} weight="bold" className="text-green-600" />
                  <span className="text-sm font-mono text-[#09090B]">{doc.file_name}</span>
                </div>
                <span className="text-xs text-[#52525B]">
                  {(doc.file_size / 1024).toFixed(0)} KB
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentHelper;
