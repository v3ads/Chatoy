import type { Metadata } from "next";
import Footer from "@/components/Footer";
import Nav from "@/components/Nav";
import { LegalShell, P, H2, UL } from "@/components/Legal";

export const metadata: Metadata = { title: "Terms of Service — MythoStack" };

export default function TermsPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Nav />
      <LegalShell title="Terms of Service" updated="May 21, 2026">
        <P>
          These Terms of Service (&ldquo;Terms&rdquo;) govern your access to and
          use of MythoStack (the &ldquo;Service&rdquo;). By creating an account or
          using the Service, you agree to these Terms. If you do not agree, do not
          use the Service.
        </P>

        <H2>The Service</H2>
        <P>
          MythoStack provides AI-assisted marketing strategy and copywriting. It
          interviews you, proposes an asset to build, and generates copy in a voice
          derived from samples you provide.
        </P>

        <H2>Accounts and eligibility</H2>
        <UL
          items={[
            "You must be at least 16 (or the age of majority where you live) and able to form a binding contract.",
            "You are responsible for your account credentials and all activity under your account.",
            "Provide accurate information and keep it current.",
          ]}
        />

        <H2>Acceptable use</H2>
        <P>You agree not to use the Service to:</P>
        <UL
          items={[
            "Break the law or infringe others' rights, including intellectual property and privacy rights.",
            "Generate deceptive, fraudulent, harassing, hateful, or otherwise harmful content.",
            "Upload content you do not have the right to use, including others' writing without permission.",
            "Reverse engineer, scrape, overload, or attempt to disrupt or gain unauthorized access to the Service.",
          ]}
        />

        <H2>Your content and AI output</H2>
        <UL
          items={[
            "You retain ownership of the content you submit (your inputs).",
            "As between you and us, you own the marketing copy generated for you (the outputs), subject to these Terms and any third-party rights.",
            "AI output may be inaccurate, may resemble output provided to others, and is not guaranteed to achieve any result. You are responsible for reviewing and for ensuring outputs comply with applicable laws (including advertising and disclosure rules) before use.",
            "You grant us a limited license to process your content solely to operate and provide the Service.",
          ]}
        />

        <H2>Payment and subscriptions</H2>
        <UL
          items={[
            "Paid plans are billed in advance on a recurring basis through our payment processor. Usage-based points may apply, with optional top-ups.",
            "Fees are non-refundable except where required by law. You can cancel anytime; cancellation takes effect at the end of the current billing period.",
            "We may change pricing with reasonable advance notice.",
          ]}
        />

        <H2>Termination</H2>
        <P>
          You may stop using the Service at any time. We may suspend or terminate
          your access if you violate these Terms or to protect the Service. Upon
          termination, your right to use the Service ends; certain provisions
          survive (including ownership, disclaimers, and limitation of liability).
        </P>

        <H2>Disclaimers</H2>
        <P>
          The Service is provided &ldquo;as is&rdquo; and &ldquo;as
          available,&rdquo; without warranties of any kind, whether express or
          implied, including merchantability, fitness for a particular purpose, and
          non-infringement. We do not warrant that the Service will be
          uninterrupted, error-free, or that AI outputs will be accurate or
          effective.
        </P>

        <H2>Limitation of liability</H2>
        <P>
          To the maximum extent permitted by law, MythoStack will not be liable for
          any indirect, incidental, special, consequential, or punitive damages, or
          for lost profits or revenues. Our total liability for any claim relating
          to the Service will not exceed the amount you paid us in the 12 months
          before the event giving rise to the claim.
        </P>

        <H2>Indemnification</H2>
        <P>
          You agree to indemnify and hold MythoStack harmless from claims arising
          out of your content, your use of the Service, or your violation of these
          Terms or applicable law.
        </P>

        <H2>Governing law</H2>
        <P>
          These Terms are governed by the laws of [your governing jurisdiction],
          without regard to conflict-of-laws rules. Replace this with your chosen
          jurisdiction before launch.
        </P>

        <H2>Changes</H2>
        <P>
          We may update these Terms from time to time. We will post the updated
          version with a new effective date; continued use after changes means you
          accept them.
        </P>

        <H2>Contact</H2>
        <P>Questions about these Terms? Email legal@mythostack.com.</P>
      </LegalShell>
      <Footer />
    </div>
  );
}
