import type { Metadata } from "next";
import Footer from "@/components/Footer";
import Nav from "@/components/Nav";
import { LegalShell, P, H2, UL } from "@/components/Legal";

export const metadata: Metadata = { title: "Privacy Policy — MythoStack" };

export default function PrivacyPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Nav />
      <LegalShell title="Privacy Policy" updated="May 21, 2026">
        <P>
          This Privacy Policy explains how MythoStack (&ldquo;MythoStack,&rdquo;
          &ldquo;we,&rdquo; &ldquo;us&rdquo;) collects, uses, and shares
          information when you use our website and application (the
          &ldquo;Service&rdquo;). By using the Service you agree to this Policy.
        </P>

        <H2>Information we collect</H2>
        <UL
          items={[
            "Account information: your email address and authentication identifiers, managed through our auth provider (Supabase).",
            "Content you submit: messages, business details, writing samples you upload to build your voice profile, and the marketing assets generated for you.",
            "Performance data: metrics you choose to log about how your assets performed.",
            "Usage and technical data: log data, approximate location derived from IP, device/browser information, and product usage events.",
            "Payment information: if you subscribe, billing is handled by our payment processor (Stripe). We do not store full card numbers.",
          ]}
        />

        <H2>How we use information</H2>
        <UL
          items={[
            "To provide the Service: run the strategy conversation, analyze your voice, generate copy, and remember past results.",
            "To process your content with AI: prompts and relevant context are sent to our model provider (Anthropic) to produce responses.",
            "To operate, secure, debug, and improve the Service.",
            "To process payments and manage your subscription.",
            "To communicate with you about your account and the Service.",
          ]}
        />

        <H2>AI processing</H2>
        <P>
          To generate strategy and copy, the content you provide is transmitted
          to our AI subprocessor (Anthropic) for processing. We do not sell your
          content, and we do not use your private content to train third-party
          models beyond what is necessary to return your results.
        </P>

        <H2>Subprocessors and sharing</H2>
        <P>We share information with service providers who process it on our behalf, including:</P>
        <UL
          items={[
            "Anthropic — AI model inference.",
            "Supabase — authentication and database.",
            "Hosting providers (e.g., Railway, Vercel) — running the application.",
            "Stripe — payment processing.",
          ]}
        />
        <P>
          We may also disclose information to comply with the law, enforce our
          terms, or protect the rights, safety, and security of our users and the
          Service. We may share information in connection with a merger,
          acquisition, or sale of assets.
        </P>

        <H2>Data retention</H2>
        <P>
          We retain your information for as long as your account is active or as
          needed to provide the Service. You may request deletion of your account
          and associated data as described below; we will delete or anonymize it
          except where we must retain it for legal, accounting, or security
          reasons.
        </P>

        <H2>Your rights</H2>
        <P>
          Depending on where you live (including under GDPR and CCPA/CPRA), you
          may have the right to access, correct, export, or delete your personal
          information, and to object to or restrict certain processing. To
          exercise these rights, contact us at privacy@mythostack.com.
        </P>

        <H2>Cookies and local storage</H2>
        <P>
          We use cookies and browser local storage to keep you logged in and to
          remember preferences. You can control cookies through your browser
          settings, though some features may not work without them.
        </P>

        <H2>Security</H2>
        <P>
          We use reasonable technical and organizational measures to protect your
          information, including encryption in transit and tenant isolation. No
          method of transmission or storage is completely secure, so we cannot
          guarantee absolute security.
        </P>

        <H2>International transfers</H2>
        <P>
          Your information may be processed in countries other than where you
          live, including the United States. Where required, we rely on
          appropriate safeguards for such transfers.
        </P>

        <H2>Children</H2>
        <P>
          The Service is not directed to children under 16, and we do not
          knowingly collect their personal information.
        </P>

        <H2>Changes</H2>
        <P>
          We may update this Policy from time to time. We will post the updated
          version with a new effective date and, where appropriate, notify you.
        </P>

        <H2>Contact</H2>
        <P>Questions? Email privacy@mythostack.com.</P>
      </LegalShell>
      <Footer />
    </div>
  );
}
