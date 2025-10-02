export interface ParsedEmailInfo {
  subject?: string;
  senderName?: string;
  senderEmail?: string;
  senderRole?: string;
  content: string;
}


export function parseEmailContent(emailText: string): ParsedEmailInfo {
  const lines = emailText.split('\n').map(line => line.trim()).filter(Boolean);
  
  const result: ParsedEmailInfo = {
    content: emailText
  };


  const subjectLine = lines.find(line => 
    /^Assunto:/i.test(line) || /^Subject:/i.test(line)
  );
  if (subjectLine) {
    result.subject = subjectLine.replace(/^(Assunto|Subject):\s*/i, '').trim();
  }


  const emailRegex = /([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/;
  const emailMatch = emailText.match(emailRegex);
  if (emailMatch) {
    result.senderEmail = emailMatch[1];
  }

 
  const signatureIndex = lines.findIndex(line => 
    /^(Atenciosamente|Cordialmente|Abraços|At\.te|Att)/i.test(line)
  );
  
  if (signatureIndex !== -1 && signatureIndex < lines.length - 1) {

    const afterSignature = lines.slice(signatureIndex + 1);
    

    const nameCandidate = afterSignature.find(line => 
      line.length > 0 && 
      !emailRegex.test(line) && 
      !/@/.test(line) &&
      !/^\(?\d{2}\)?/.test(line) 
    );
    
    if (nameCandidate) {
      result.senderName = nameCandidate;
      

      const nameIndex = afterSignature.indexOf(nameCandidate);
      if (nameIndex !== -1 && nameIndex < afterSignature.length - 1) {
        const roleCandidate = afterSignature[nameIndex + 1];
        if (roleCandidate && 
            !emailRegex.test(roleCandidate) && 
            !/@/.test(roleCandidate) &&
            !/^\(?\d{2}\)?/.test(roleCandidate)) {
          result.senderRole = roleCandidate;
        }
      }
    }
  }

  return result;
}
