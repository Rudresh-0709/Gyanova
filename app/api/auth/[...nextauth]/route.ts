
import NextAuth from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"

const handler = NextAuth({
    providers: [
        CredentialsProvider({
            name: 'Demo Account',
            credentials: {},
            async authorize(credentials, req) {
                // Mock a successful login for any attempt
                // This allows you to test the protected routes and UI
                // without setting up OAuth.
                return {
                    id: "1",
                    name: "Demo User",
                    email: "demo@gyanova.com",
                    image: "https://ui-avatars.com/api/?name=Demo+User&background=6366f1&color=fff"
                }
            }
        })
    ],
    callbacks: {
        async redirect({ url, baseUrl }) {
            // Redirect to lesson creation page after sign in
            if (url.startsWith("/")) return `${baseUrl}${url}`
            else if (new URL(url).origin === baseUrl) return url
            return baseUrl + "/lesson/new"
        },
    },
    pages: {
        // optional custom pages
        // signIn: '/auth/signin',
    }
})

export { handler as GET, handler as POST }
